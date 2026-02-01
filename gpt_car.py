from openai_helper import OpenAiHelper
from keys import OPENAI_API_KEY, OPENAI_ASSISTANT_ID
from preset_actions import actions_dict, sounds_dict
from utils import gray_print, speak_block, sox_volume, redirect_error_2_null, cancel_redirect_error
from visual_tracking import create_visual_tracking_handler

# readline només s'utilitza per optimitzar input de teclat, però pot fallar sense TTY
try:
    import readline  # optimize keyboard input, only need to import
except (ImportError, OSError):
    # Si readline no està disponible o no hi ha TTY, continuar sense ell
    pass

import speech_recognition as sr

from picarx import Picarx
from robot_hat import Music, Pin

import time
import threading
import random
import tempfile

import os
import sys

# Forcem que os.getlogin retorni l'usuari correcte sense buscar un terminal
try:
    import pwd
    def mocked_getlogin():
        return pwd.getpwuid(os.getuid())[0]
    os.getlogin = mocked_getlogin
except (ImportError, OSError):
    # Si pwd no està disponible (Windows), usar os.getenv('USER') o similar
    def mocked_getlogin():
        return os.getenv('USER', os.getenv('USERNAME', 'user'))
    os.getlogin = mocked_getlogin

os.environ['SDL_AUDIODRIVER'] = 'pulse' # PipeWire a Bookworm emula PulseAudio - necessary per a que raspberry pi 4 to work with sound

# Enable robot_hat speaker switch
try:
    proc = os.popen("pinctrl set 20 op dh")
    proc.close()  # Tancar el procés per evitar resource leaks
except Exception as e:
    print(f'Warning: Could not enable speaker switch: {e}')
current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path) # change working directory

# Ensure required directories exist with proper permissions
tts_dir = os.path.join(current_path, 'tts')
os.makedirs(tts_dir, mode=0o755, exist_ok=True)

input_mode = None
with_img = True
args = sys.argv[1:]

# Comprovar si hi ha TTY disponible
has_tty = sys.stdin.isatty() if hasattr(sys.stdin, 'isatty') else False

if '--keyboard' in args:
    if has_tty:
        input_mode = 'keyboard'
    else:
        print('Warning: --keyboard especificat però no hi ha TTY disponible. Usant mode voice.')
        input_mode = 'voice'
else:
    input_mode = 'voice'

if '--no-img' in args:
    with_img = False
else:
    with_img = True

# openai assistant init
# =================================================================
openai_helper = OpenAiHelper(OPENAI_API_KEY, OPENAI_ASSISTANT_ID, 'picarx')

LANGUAGE = 'ca'  # Catalan language code for STT
VOLUME_DB = 3

# Validar VOLUME_DB dins d'un rang raonable (0-10 per evitar distorsió)
if not isinstance(VOLUME_DB, (int, float)) or VOLUME_DB < 0 or VOLUME_DB > 10:
    print(f'Warning: VOLUME_DB={VOLUME_DB} està fora del rang recomanat (0-10). Usant valor per defecte 3.')
    VOLUME_DB = 3

# select tts voice role, counld be "alloy, echo, fable, onyx, nova, and shimmer"
# https://platform.openai.com/docs/guides/text-to-speech/supported-languages
TTS_VOICE = 'echo'

# voice instructions for vibe
# https://www.openai.fm/
VOICE_INSTRUCTIONS = ""

SOUND_EFFECT_ACTIONS = ["honking", "start engine"]

# car init 
try:
    my_car = Picarx()
    time.sleep(1)
except Exception as e:
    # Preservar la traça completa de l'excepció original
    raise RuntimeError(f"Error inicialitzant Picarx: {e}") from e

music = Music()

led = Pin('LED')

DEFAULT_HEAD_PAN = 0
DEFAULT_HEAD_TILT = 20

# Vilib start
if with_img:
    from vilib import Vilib
    import cv2
    os.environ['FLASK_CHDIR'] = current_path
    Vilib.camera_start(vflip=False,hflip=False)
    Vilib.show_fps()
    Vilib.display(local=False,web=True)
    Vilib.face_detect_switch(True)  # Activar detecció de persones

    while True:
        if Vilib.flask_start:
            break
        time.sleep(0.01)

    time.sleep(.5)
    print('\n')

# speech_recognition init
recognizer = sr.Recognizer()
recognizer.dynamic_energy_adjustment_damping = 0.16
recognizer.dynamic_energy_ratio = 1.6

# speak_hanlder
speech_loaded = False
speech_lock = threading.Lock()
tts_file = None
# Ref compartida per sincronitzar speak_handler amb wait_for_speech_completion (el bucle principal escriu als refs, el speak_handler llegeix les globals i actualitza el ref quan acaba)
_speech_loaded_ref = None

def speak_hanlder():
    global speech_loaded, tts_file
    while True:
        with speech_lock:
            _isloaded = speech_loaded
        if _isloaded:
            # gray_print('speak start')
            speak_block(music, tts_file)
            # gray_print('speak done')
            with speech_lock:
                speech_loaded = False
                if _speech_loaded_ref is not None:
                    _speech_loaded_ref['speech_loaded'] = False
        time.sleep(0.05)

speak_thread = threading.Thread(target=speak_hanlder)
speak_thread.daemon = True


# actions thread
action_status = 'standby' # 'standby', 'think', 'actions', 'actions_done'
led_status = 'standby' # 'standby', 'think' or 'actions', 'actions_done'
last_action_status = 'standby'
last_led_status = 'standby'

LED_DOUBLE_BLINK_INTERVAL = 0.8 # seconds
LED_BLINK_INTERVAL = 0.1 # seconds

actions_to_be_done = []
action_lock = threading.Lock()


def update_led_status(new_status, last_status, last_led_time):
    """
    Actualitza l'estat del LED i retorna el nou temps si ha canviat.
    
    Returns:
        tuple: (nou_led_time, nou_last_status)
    """
    if new_status != last_status:
        return (0, new_status)
    return (last_led_time, last_status)


def handle_led_standby_blink(led_pin, current_time, last_led_time):
    """
    Gestiona el parpelleig doble del LED en estat standby.
    
    Returns:
        float: Nou temps de LED després del parpelleig, o None si no s'ha fet
    """
    if current_time - last_led_time > LED_DOUBLE_BLINK_INTERVAL:
        led_pin.off()
        led_pin.on()
        time.sleep(.1)
        led_pin.off()
        time.sleep(.1)
        led_pin.on()
        time.sleep(.1)
        led_pin.off()
        return current_time
    return None


def handle_led_think_blink(led_pin, current_time, last_led_time):
    """
    Gestiona el parpelleig del LED en estat think.
    
    Returns:
        float: Nou temps de LED després del parpelleig, o None si no s'ha fet
    """
    if current_time - last_led_time > LED_BLINK_INTERVAL:
        led_pin.off()
        time.sleep(LED_BLINK_INTERVAL)
        led_pin.on()
        time.sleep(LED_BLINK_INTERVAL)
        return current_time
    return None


def handle_led_actions(led_pin):
    """Gestiona el LED en estat actions (encès constantment)."""
    led_pin.on()


def process_led_status(led_pin, led_status, last_led_status, last_led_time):
    """
    Processa l'estat del LED i actualitza el parpelleig segons l'estat.
    
    Returns:
        tuple: (nou_last_led_time, nou_last_led_status)
    """
    current_time = time.time()
    new_led_time, new_last_status = update_led_status(led_status, last_led_status, last_led_time)
    
    if led_status == 'standby':
        updated_time = handle_led_standby_blink(led_pin, current_time, new_led_time)
        if updated_time is not None:
            return (updated_time, new_last_status)
    elif led_status == 'think':
        updated_time = handle_led_think_blink(led_pin, current_time, new_led_time)
        if updated_time is not None:
            return (updated_time, new_last_status)
    elif led_status == 'actions':
        handle_led_actions(led_pin)
    
    return (new_led_time, new_last_status)


def handle_standby_state(last_action_time, action_interval):
    """
    Gestiona l'estat standby i retorna el nou interval d'acció si cal.
    
    Returns:
        tuple: (nou_last_action_time, nou_action_interval, ha_canviat)
    """
    current_time = time.time()
    if current_time - last_action_time > action_interval:
        new_interval = random.randint(2, 6)
        return (current_time, new_interval, True)
    return (last_action_time, action_interval, False)


def handle_think_state(last_action_status):
    """
    Gestiona l'estat think.
    
    Returns:
        str: Nou estat d'acció
    """
    if last_action_status != 'think':
        return 'think'
    return last_action_status


def execute_actions_list(actions_list, car, action_lock_ref, action_status_ref):
    """
    Executa una llista d'accions sobre el cotxe.
    
    Args:
        actions_list: Llista d'accions a executar
        car: Instància de Picarx
        action_lock_ref: Referència al lock d'accions
        action_status_ref: Referència a la variable action_status (per actualitzar-la)
    """
    for _action in actions_list:
        try:
            actions_dict[_action](car)
        except Exception as e:
            print(f'action error: {e}')
        time.sleep(0.5)
    
    with action_lock_ref:
        action_status_ref['action_status'] = 'actions_done'


def handle_action_state(state, last_action_status, last_action_time, action_interval, 
                        actions_to_be_done_ref, action_lock_ref, action_status_ref, car):
    """
    Gestiona l'estat de les accions segons l'estat actual.
    
    Returns:
        tuple: (nou_last_action_status, nou_last_action_time, nou_action_interval)
    """
    if state == 'standby':
        new_last_action_time, new_action_interval, _ = handle_standby_state(last_action_time, action_interval)
        return ('standby', new_last_action_time, new_action_interval)
    elif state == 'think':
        new_last_action_status = handle_think_state(last_action_status)
        return (new_last_action_status, last_action_time, action_interval)
    elif state == 'actions':
        with action_lock_ref:
            _actions = actions_to_be_done_ref['actions_to_be_done']
        execute_actions_list(_actions, car, action_lock_ref, action_status_ref)
        return ('actions', time.time(), action_interval)
    
    return (last_action_status, last_action_time, action_interval)


def action_handler():
    global action_status, actions_to_be_done, led_status, last_action_status, last_led_status

    action_interval = 5 # seconds
    last_action_time = time.time()
    last_led_time = time.time()

    # Crear referències mutables per poder actualitzar action_status des de funcions
    action_status_ref = {'action_status': action_status}
    actions_to_be_done_ref = {'actions_to_be_done': actions_to_be_done}

    while True:
        with action_lock:
            _state = action_status
            action_status_ref['action_status'] = action_status

        # led
        led_status = _state
        last_led_time, last_led_status = process_led_status(
            led, led_status, last_led_status, last_led_time
        )

        # actions
        last_action_status, last_action_time, action_interval = handle_action_state(
            _state, last_action_status, last_action_time, action_interval,
            actions_to_be_done_ref, action_lock, action_status_ref, my_car
        )
        
        # Sincronitzar action_status global amb la referència
        with action_lock:
            action_status = action_status_ref['action_status']

        time.sleep(0.01)

action_thread = threading.Thread(target=action_handler)
action_thread.daemon = True

# person detection thread - detecta persones i diu "Hola"
person_detected = False
person_detection_lock = threading.Lock()
GREETING_COOLDOWN = 5.0  # segons d'espera abans de tornar a saludar la mateixa persona
last_greeting_time = 0

def person_detection_handler():
    """Fil que detecta persones i fa que el robot digui 'Hola'"""
    global person_detected, last_greeting_time, speech_loaded, tts_file, tts_dir
    
    if not with_img:
        return
    
    # Esperar una mica per assegurar que Vilib està completament inicialitzat
    time.sleep(1.0)
    
    while True:
        try:
            # Comprovar si hi ha una persona detectada (validar que existeixi el paràmetre)
            if (hasattr(Vilib, 'detect_obj_parameter') and 
                isinstance(Vilib.detect_obj_parameter, dict) and
                Vilib.detect_obj_parameter.get('human_n', 0) != 0):
                # Persona detectada
                with person_detection_lock:
                    current_time = time.time()
                    # Només saludar si no hem saludat recentment
                    if not person_detected or (current_time - last_greeting_time) > GREETING_COOLDOWN:
                        person_detected = True
                        last_greeting_time = current_time
                        
                        # Generar TTS per dir "Hola"
                        gray_print("Persona detectada! Dient 'Hola'...")
                        try:
                            _time = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
                            _tts_f = os.path.join(tts_dir, f"greeting_{_time}_raw.wav")
                            _tts_status = openai_helper.text_to_speech(
                                "Hola", 
                                _tts_f, 
                                TTS_VOICE, 
                                response_format='wav', 
                                instructions=VOICE_INSTRUCTIONS
                            )
                            if _tts_status:
                                tts_file = os.path.join(tts_dir, f"greeting_{_time}_{VOLUME_DB}dB.wav")
                                _tts_status = sox_volume(_tts_f, tts_file, VOLUME_DB)
                                if _tts_status:
                                    # Activar la reproducció del so
                                    with speech_lock:
                                        speech_loaded = True
                        except Exception as e:
                            print(f'Error en TTS de salutació: {e}')
            else:
                # No hi ha persona detectada
                with person_detection_lock:
                    person_detected = False
                    
        except Exception as e:
            print(f'Error en detecció de persones: {e}')
        
        time.sleep(0.2)  # Comprovar cada 200ms

person_detection_thread = threading.Thread(target=person_detection_handler)
person_detection_thread.daemon = True


# visual tracking thread - seguiment visual pur amb càmera (FASE 1, PAS 2 i 3)
# Crear handler de seguiment visual (Vilib ja està importat abans si with_img)
Vilib_module = Vilib if with_img and 'Vilib' in globals() else None
visual_tracking_handler, visual_tracking_state, visual_tracking_lock, is_person_centered = create_visual_tracking_handler(
    my_car, 
    Vilib_module, 
    with_img, 
    DEFAULT_HEAD_TILT
)

visual_tracking_thread = threading.Thread(target=visual_tracking_handler)
visual_tracking_thread.daemon = True


# Funcions auxiliars per a main()


def reset_camera_if_needed(car, with_img_flag):
    """
    Reseteja la càmera si no hi ha seguiment visual actiu.
    
    Args:
        car: Instància de Picarx
        with_img_flag: Si hi ha imatge disponible
    """
    if not with_img_flag:
        car.set_cam_pan_angle(DEFAULT_HEAD_PAN)
        car.set_cam_tilt_angle(DEFAULT_HEAD_TILT)


def get_voice_input(recognizer_obj, openai_helper_obj, language, action_lock_ref, action_status_ref, car, with_img_flag):
    """
    Obté input de veu mitjançant el micròfon i STT.
    
    Returns:
        str: Text reconegut, o None si no s'ha pogut obtenir
    """
    # No resetar càmera si el seguiment visual està actiu
    # El seguiment visual controla els angles de la càmera contínuament
    reset_camera_if_needed(car, with_img_flag)

    # listen
    gray_print("listening ...")

    with action_lock_ref:
        action_status_ref['action_status'] = 'standby'

    _stderr_back = redirect_error_2_null() # ignore error print to ignore ALSA errors
    # If the chunk_size is set too small (default_size=1024), it may cause the program to freeze
    with sr.Microphone(chunk_size=4096) as source:
        cancel_redirect_error(_stderr_back) # restore error print
        recognizer_obj.adjust_for_ambient_noise(source)
        audio = recognizer_obj.listen(source)

    # stt
    gray_print('stt ...')
    st = time.time()
    _result = openai_helper_obj.stt(audio, language=language)
    gray_print(f"stt takes: {time.time() - st:.3f} s")

    if not _result or _result == "":
        return None
    return _result


def get_keyboard_input(action_lock_ref, action_status_ref, car, with_img_flag):
    """
    Obté input de teclat.
    
    Returns:
        tuple: (text_input, should_continue, input_mode_changed)
        - text_input: Text introduït, o None si està buit
        - should_continue: Si cal continuar el bucle
        - input_mode_changed: Si s'ha canviat el mode d'input
    """
    # No resetar càmera si el seguiment visual està actiu
    # El seguiment visual controla els angles de la càmera contínuament
    reset_camera_if_needed(car, with_img_flag)

    with action_lock_ref:
        action_status_ref['action_status'] = 'standby'

    try:
        _result = input(f'\033[1;30m{"input: "}\033[0m').encode(sys.stdin.encoding).decode('utf-8')
    except (EOFError, OSError) as e:
        # Si no hi ha TTY disponible, canviar a mode voice
        print(f'Error: No TTY disponible per input de teclat: {e}')
        print('Canviant a mode voice...')
        return (None, True, True)

    if not _result or _result == "":
        return (None, True, False)
    
    return (_result, False, False)


def get_user_input(input_mode_val, recognizer_obj, openai_helper_obj, language, 
                   action_lock_ref, action_status_ref, car, with_img_flag):
    """
    Obté input de l'usuari segons el mode (voice o keyboard).
    
    Returns:
        tuple: (text_input, should_continue, input_mode_changed, new_input_mode)
    """
    if input_mode_val == 'voice':
        result = get_voice_input(recognizer_obj, openai_helper_obj, language, 
                                action_lock_ref, action_status_ref, car, with_img_flag)
        if result is None:
            return (None, True, False, input_mode_val)
        return (result, False, False, input_mode_val)
    elif input_mode_val == 'keyboard':
        result, should_continue, input_mode_changed = get_keyboard_input(
            action_lock_ref, action_status_ref, car, with_img_flag
        )
        new_mode = 'voice' if input_mode_changed else input_mode_val
        return (result, should_continue, input_mode_changed, new_mode)
    else:
        raise ValueError("Invalid input mode")


def capture_image(current_path_val, vilib_module=None):
    """
    Captura una imatge de la càmera i la guarda a un fitxer.
    
    Returns:
        str: Ruta al fitxer d'imatge, o None si no s'ha pogut capturar
    """
    if vilib_module is None:
        return None
    
    img_path = os.path.join(current_path_val, 'img_input.jpg')
    try:
        # Validar que Vilib.img existeixi i sigui vàlid abans d'escriure
        if not hasattr(vilib_module, 'img') or vilib_module.img is None:
            raise ValueError("Vilib.img no està disponible")
        cv2.imwrite(img_path, vilib_module.img)
        return img_path
    except (ValueError, AttributeError, Exception) as e:
        print(f'Warning: Could not write image file: {e}')
        # Try alternative location
        try:
            img_path = os.path.join(tempfile.gettempdir(), 'img_input.jpg')
            if hasattr(vilib_module, 'img') and vilib_module.img is not None:
                cv2.imwrite(img_path, vilib_module.img)
                return img_path
            else:
                print('Warning: Vilib.img no disponible, continuant sense imatge')
                return None
        except Exception as e2:
            print(f'Warning: Could not write image to temp directory: {e2}')
            return None


def get_gpt_response(user_input, openai_helper_obj, with_img_flag, vilib_module=None, 
                     current_path_val=None):
    """
    Obté la resposta de GPT per a l'input de l'usuari.
    
    Returns:
        dict: Resposta de GPT
    """
    gray_print(f'thinking ...')
    st = time.time()

    if with_img_flag:
        img_path = capture_image(current_path_val, vilib_module)
        
        # Només usar imatge si s'ha pogut crear correctament
        if img_path:
            response = openai_helper_obj.dialogue_with_img(user_input, img_path)
        else:
            # Fallback a diàleg sense imatge si no es pot obtenir la imatge
            print('Warning: Continuant sense imatge degut a errors previs')
            response = openai_helper_obj.dialogue(user_input)
    else:
        response = openai_helper_obj.dialogue(user_input)

    gray_print(f'chat takes: {time.time() - st:.3f} s')
    return response


def _extract_actions_from_dict(response_dict):
    """Extreu les accions d'un diccionari de resposta."""
    if 'actions' in response_dict:
        return list(response_dict['actions'])
    return ['stop']


def _extract_answer_from_dict(response_dict):
    """Extreu la resposta d'un diccionari de resposta."""
    return response_dict.get('answer', '')


def _separate_sound_actions(actions, answer, sound_effect_actions):
    """
    Separa les accions que són efectes de so de les accions normals.
    
    Returns:
        tuple: (filtered_actions, sound_actions)
    """
    if not answer:
        return actions, []
    
    sound_actions = []
    filtered_actions = []
    
    for action in actions:
        if action in sound_effect_actions:
            sound_actions.append(action)
        else:
            filtered_actions.append(action)
    
    return filtered_actions, sound_actions


def _parse_dict_response(response_dict, sound_effect_actions):
    """Processa una resposta que és un diccionari."""
    actions = _extract_actions_from_dict(response_dict)
    answer = _extract_answer_from_dict(response_dict)
    actions, sound_actions = _separate_sound_actions(actions, answer, sound_effect_actions)
    return actions, answer, sound_actions


def _parse_string_response(response):
    """Processa una resposta que és un string."""
    response_str = str(response)
    if response_str:
        return [], response_str, []
    return [], '', []


def parse_gpt_response(response, sound_effect_actions):
    """
    Parseja la resposta de GPT i extreu accions, resposta i efectes de so.
    
    Returns:
        tuple: (actions, answer, sound_actions)
    """
    try:
        if isinstance(response, dict):
            return _parse_dict_response(response, sound_effect_actions)
        else:
            return _parse_string_response(response)
    except Exception as e:
        print(f'Warning: Error processant resposta de GPT: {e}')
        return [], '', []


def generate_tts(answer, openai_helper_obj, tts_dir_path, tts_voice, volume_db, 
                 voice_instructions, tts_file_ref):
    """
    Genera TTS per a una resposta.
    
    Returns:
        bool: True si s'ha generat correctament, False altrament
    """
    if answer == '':
        return False
    
    st = time.time()
    _time = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
    _tts_f = os.path.join(tts_dir_path, f"{_time}_raw.wav")
    _tts_status = openai_helper_obj.text_to_speech(
        answer, _tts_f, tts_voice, response_format='wav', instructions=voice_instructions
    )
    if _tts_status:
        tts_file_ref['tts_file'] = os.path.join(tts_dir_path, f"{_time}_{volume_db}dB.wav")
        _tts_status = sox_volume(_tts_f, tts_file_ref['tts_file'], volume_db)
    gray_print(f'tts takes: {time.time() - st:.3f} s')
    return _tts_status


def execute_actions_and_sounds(actions_list, sound_actions_list, music_obj, 
                               action_lock_ref, action_status_ref, actions_to_be_done_ref):
    """
    Executa les accions i els efectes de so.
    """
    # ---- actions ----
    with action_lock_ref:
        actions_to_be_done_ref['actions_to_be_done'] = actions_list
        gray_print(f'actions: {actions_list}')
        action_status_ref['action_status'] = 'actions'

    # --- sound effects and voice ---
    for _sound in sound_actions_list:
        try:
            sounds_dict[_sound](music_obj)
        except Exception as e:
            print(f'action error: {e}')


def wait_for_speech_completion(speech_lock_ref, speech_loaded_ref):
    """
    Espera que acabi la reproducció de veu.
    """
    while True:
        with speech_lock_ref:
            if not speech_loaded_ref['speech_loaded']:
                break
        time.sleep(.01)


def wait_for_actions_completion(action_lock_ref, action_status_ref):
    """
    Espera que acabin les accions.
    """
    while True:
        with action_lock_ref:
            if action_status_ref['action_status'] != 'actions':
                break
        time.sleep(.01)


def process_user_query(user_input, config, action_state, speech_state, tts_config):
    """
    Processa una consulta de l'usuari: obté resposta de GPT, genera TTS i executa accions.
    
    Args:
        user_input: Text de l'usuari
        config: Diccionari amb configuració {
            'openai_helper': OpenAiHelper instance,
            'with_img': bool,
            'vilib_module': Vilib module o None,
            'current_path': str,
            'music': Music instance,
            'sound_effect_actions': list
        }
        action_state: Diccionari amb estat d'accions {
            'lock': threading.Lock,
            'status_ref': dict amb 'action_status',
            'actions_to_be_done_ref': dict amb 'actions_to_be_done'
        }
        speech_state: Diccionari amb estat de veu {
            'lock': threading.Lock,
            'loaded_ref': dict amb 'speech_loaded',
            'tts_file_ref': dict amb 'tts_file'
        }
        tts_config: Diccionari amb configuració TTS {
            'dir_path': str,
            'voice': str,
            'volume_db': int/float,
            'instructions': str
        }
    """
    # chat-gpt
    with action_state['lock']:
        action_state['status_ref']['action_status'] = 'think'

    response = get_gpt_response(
        user_input, config['openai_helper'], config['with_img'],
        config.get('vilib_module'), config.get('current_path')
    )

    # actions & TTS
    actions, answer, sound_actions = parse_gpt_response(
        response, config['sound_effect_actions']
    )

    try:
        # ---- tts ----
        tts_status = generate_tts(
            answer, config['openai_helper'], tts_config['dir_path'],
            tts_config['voice'], tts_config['volume_db'],
            tts_config['instructions'], speech_state['tts_file_ref']
        )

        # ---- actions ----
        execute_actions_and_sounds(
            actions, sound_actions, config['music'],
            action_state['lock'], action_state['status_ref'],
            action_state['actions_to_be_done_ref']
        )

        if tts_status:
            with speech_state['lock']:
                speech_state['loaded_ref']['speech_loaded'] = True
            # Sincronitzar globals perquè speak_handler les llegeixi i reprodueixi
            global speech_loaded, tts_file
            speech_loaded = True
            tts_file = speech_state['tts_file_ref']['tts_file']

        # ---- wait speak done ----
        if tts_status:
            wait_for_speech_completion(speech_state['lock'], speech_state['loaded_ref'])
            gray_print("[debug] process: speech done, continuing")

        # ---- wait actions done ----
        wait_for_actions_completion(action_state['lock'], action_state['status_ref'])
        gray_print("[debug] process: actions done, continuing")

        ##
        print() # new line

    except Exception as e:
        print(f'actions or TTS error: {e}')


# main
def main():
    global current_feeling, last_feeling
    global speech_loaded
    global action_status, actions_to_be_done
    global tts_file, tts_dir
    global input_mode

    my_car.reset()
    my_car.set_cam_tilt_angle(DEFAULT_HEAD_TILT)

    speak_thread.start()
    action_thread.start()
    if with_img:
        # person_detection_thread.start()  # Desactivat: no dir "Hola" automàticament
        visual_tracking_thread.start()  # Iniciar seguiment visual pur (FASE 1, PAS 1)

    # Crear referències mutables per poder actualitzar variables des de funcions
    action_status_ref = {'action_status': action_status}
    actions_to_be_done_ref = {'actions_to_be_done': actions_to_be_done}
    speech_loaded_ref = {'speech_loaded': speech_loaded}
    tts_file_ref = {'tts_file': tts_file}
    global _speech_loaded_ref
    _speech_loaded_ref = speech_loaded_ref
    vilib_module = Vilib if with_img and 'Vilib' in globals() else None

    while True:
        user_input, should_continue, input_mode_changed, new_input_mode = get_user_input(
            input_mode, recognizer, openai_helper, LANGUAGE, action_lock, action_status_ref,
            my_car, with_img
        )
        
        if input_mode_changed:
            input_mode = new_input_mode
        
        if should_continue:
            continue

        # Agrupar paràmetres en estructures de dades
        config = {
            'openai_helper': openai_helper,
            'with_img': with_img,
            'vilib_module': vilib_module,
            'current_path': current_path,
            'music': music,
            'sound_effect_actions': SOUND_EFFECT_ACTIONS
        }
        action_state = {
            'lock': action_lock,
            'status_ref': action_status_ref,
            'actions_to_be_done_ref': actions_to_be_done_ref
        }
        speech_state = {
            'lock': speech_lock,
            'loaded_ref': speech_loaded_ref,
            'tts_file_ref': tts_file_ref
        }
        tts_config = {
            'dir_path': tts_dir,
            'voice': TTS_VOICE,
            'volume_db': VOLUME_DB,
            'instructions': VOICE_INSTRUCTIONS
        }
        
        process_user_query(user_input, config, action_state, speech_state, tts_config)
        
        # Sincronitzar variables globals amb les referències
        with action_lock:
            action_status = action_status_ref['action_status']
            actions_to_be_done = actions_to_be_done_ref['actions_to_be_done']
        with speech_lock:
            speech_loaded = speech_loaded_ref['speech_loaded']
        tts_file = tts_file_ref['tts_file']


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\033[31mERROR: {e}\033[m")
    finally:
        if with_img:
            Vilib.camera_close()
        my_car.reset()

