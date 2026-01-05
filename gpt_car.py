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

def action_handler():
    global action_status, actions_to_be_done, led_status, last_action_status, last_led_status

    action_interval = 5 # seconds
    last_action_time = time.time()
    last_led_time = time.time()

    while True:
        with action_lock:
            _state = action_status

        # led
        led_status = _state

        if led_status != last_led_status:
            last_led_time = 0
            last_led_status = led_status

        if led_status == 'standby':
            if time.time() - last_led_time > LED_DOUBLE_BLINK_INTERVAL:
                led.off()
                led.on()
                sleep(.1)
                led.off()
                sleep(.1)
                led.on()
                sleep(.1)
                led.off()
                last_led_time = time.time()
        elif led_status == 'think':
            if time.time() - last_led_time > LED_BLINK_INTERVAL:
                led.off()
                sleep(LED_BLINK_INTERVAL)
                led.on()
                sleep(LED_BLINK_INTERVAL)
                last_led_time = time.time()
        elif led_status == 'actions':
                led.on() 

        # actions
        if _state == 'standby':
            last_action_status = 'standby'
            if time.time() - last_action_time > action_interval:
                last_action_time = time.time()
                action_interval = random.randint(2, 6)
        elif _state == 'think':
            if last_action_status != 'think':
                last_action_status = 'think'
        elif _state == 'actions':
            last_action_status = 'actions'
            with action_lock:
                _actions = actions_to_be_done
            for _action in _actions:
                try:
                    actions_dict[_action](my_car)
                except Exception as e:
                    print(f'action error: {e}')
                time.sleep(0.5)

            with action_lock:
                action_status = 'actions_done'
            last_action_time = time.time()

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


# main
def main():
    global current_feeling, last_feeling
    global speech_loaded
    global action_status, actions_to_be_done
    global tts_file, tts_dir

    my_car.reset()
    my_car.set_cam_tilt_angle(DEFAULT_HEAD_TILT)

    speak_thread.start()
    action_thread.start()
    if with_img:
        # person_detection_thread.start()  # Desactivat: no dir "Hola" automàticament
        visual_tracking_thread.start()  # Iniciar seguiment visual pur (FASE 1, PAS 1)

    while True:
        if input_mode == 'voice':
            # No resetar càmera si el seguiment visual està actiu
            # El seguiment visual controla els angles de la càmera contínuament
            if not with_img:
                my_car.set_cam_pan_angle(DEFAULT_HEAD_PAN)
                my_car.set_cam_tilt_angle(DEFAULT_HEAD_TILT)

            # listen
            gray_print("listening ...")

            with action_lock:
                action_status = 'standby'

            _stderr_back = redirect_error_2_null() # ignore error print to ignore ALSA errors
            # If the chunk_size is set too small (default_size=1024), it may cause the program to freeze
            with sr.Microphone(chunk_size=8192) as source:
                cancel_redirect_error(_stderr_back) # restore error print
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)

            # stt
            gray_print('stt ...')
            st = time.time()
            _result = openai_helper.stt(audio, language=LANGUAGE)
            gray_print(f"stt takes: {time.time() - st:.3f} s")

            if not _result or _result == "":
                print() # new line
                continue

        elif input_mode == 'keyboard':
            # No resetar càmera si el seguiment visual està actiu
            # El seguiment visual controla els angles de la càmera contínuament
            if not with_img:
                my_car.set_cam_tilt_angle(DEFAULT_HEAD_TILT)

            with action_lock:
                action_status = 'standby'

            try:
                _result = input(f'\033[1;30m{"input: "}\033[0m').encode(sys.stdin.encoding).decode('utf-8')
            except (EOFError, OSError) as e:
                # Si no hi ha TTY disponible, canviar a mode voice
                print(f'Error: No TTY disponible per input de teclat: {e}')
                print('Canviant a mode voice...')
                input_mode = 'voice'
                continue

            if not _result or _result == "":
                print() # new line
                continue

        else:
            raise ValueError("Invalid input mode")

        # chat-gpt
        gray_print(f'thinking ...')
        response = {}
        st = time.time()

        with action_lock:
            action_status = 'think'

        if with_img:
            img_path = os.path.join(current_path, 'img_input.jpg')
            try:
                # Validar que Vilib.img existeixi i sigui vàlid abans d'escriure
                if not hasattr(Vilib, 'img') or Vilib.img is None:
                    raise ValueError("Vilib.img no està disponible")
                cv2.imwrite(img_path, Vilib.img)
            except (cv2.error, ValueError, AttributeError) as e:
                print(f'Warning: Could not write image file: {e}')
                # Try alternative location
                try:
                    img_path = os.path.join(tempfile.gettempdir(), 'img_input.jpg')
                    if hasattr(Vilib, 'img') and Vilib.img is not None:
                        cv2.imwrite(img_path, Vilib.img)
                    else:
                        print('Warning: Vilib.img no disponible, continuant sense imatge')
                        img_path = None
                except Exception as e2:
                    print(f'Warning: Could not write image to temp directory: {e2}')
                    img_path = None
            
            # Només usar imatge si s'ha pogut crear correctament
            if img_path:
                response = openai_helper.dialogue_with_img(_result, img_path)
            else:
                # Fallback a diàleg sense imatge si no es pot obtenir la imatge
                print('Warning: Continuant sense imatge degut a errors previs')
                response = openai_helper.dialogue(_result)
        else:
            response = openai_helper.dialogue(_result)

        gray_print(f'chat takes: {time.time() - st:.3f} s')

        # actions & TTS
        _sound_actions = [] 
        try:
            if isinstance(response, dict):
                if 'actions' in response:
                    actions = list(response['actions'])
                else:
                    actions = ['stop']

                if 'answer' in response:
                    answer = response['answer']
                else:
                    answer = ''

                if len(answer) > 0:
                    _actions = actions.copy()
                    for _action in _actions:
                        if _action in SOUND_EFFECT_ACTIONS:
                            _sound_actions.append(_action)
                            actions.remove(_action)

            else:
                response = str(response)
                if len(response) > 0:
                    actions = []
                    answer = response

        except Exception as e:
            # Capturar excepcions específiques en lloc de genèriques
            print(f'Warning: Error processant resposta de GPT: {e}')
            actions = []
            answer = ''
    
        try:
            # ---- tts ----
            _tts_status = False
            if answer != '':
                st = time.time()
                _time = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
                _tts_f = os.path.join(tts_dir, f"{_time}_raw.wav")
                _tts_status = openai_helper.text_to_speech(answer, _tts_f, TTS_VOICE, response_format='wav', instructions=VOICE_INSTRUCTIONS) # alloy, echo, fable, onyx, nova, and shimmer
                if _tts_status:
                    tts_file = os.path.join(tts_dir, f"{_time}_{VOLUME_DB}dB.wav")
                    _tts_status = sox_volume(_tts_f, tts_file, VOLUME_DB)
                gray_print(f'tts takes: {time.time() - st:.3f} s')

            # ---- actions ----
            with action_lock:
                actions_to_be_done = actions
                gray_print(f'actions: {actions_to_be_done}')
                action_status = 'actions'

            # --- sound effects and voice ---
            for _sound in _sound_actions:
                try:
                    sounds_dict[_sound](music)
                except Exception as e:
                    print(f'action error: {e}')

            if _tts_status:
                with speech_lock:
                    speech_loaded = True

            # ---- wait speak done ----
            if _tts_status:
                while True:
                    with speech_lock:
                        if not speech_loaded:
                            break
                    time.sleep(.01)

            # ---- wait actions done ----
            while True:
                with action_lock:
                    if action_status != 'actions':
                        break
                time.sleep(.01)

            ##
            print() # new line

        except Exception as e:
            print(f'actions or TTS error: {e}')


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

