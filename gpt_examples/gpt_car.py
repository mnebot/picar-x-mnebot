from openai_helper import OpenAiHelper
from keys import OPENAI_API_KEY, OPENAI_ASSISTANT_ID
from preset_actions import actions_dict, sounds_dict
from utils import gray_print, speak_block, sox_volume, redirect_error_2_null, cancel_redirect_error
from visual_tracking import create_visual_tracking_handler

import readline # optimize keyboard input, only need to import

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

os.popen("pinctrl set 20 op dh") # enable robot_hat speake switch
current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path) # change working directory

# Ensure required directories exist with proper permissions
tts_dir = os.path.join(current_path, 'tts')
os.makedirs(tts_dir, mode=0o755, exist_ok=True)

input_mode = None
with_img = True
args = sys.argv[1:]
if '--keyboard' in args:
    input_mode = 'keyboard'
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
# LANGUAGE = []  # Empty means auto-detect all languages
# LANGUAGE = ['zh', 'en'] # config stt language code, https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes

# VOLUME_DB = 5
VOLUME_DB = 3

# select tts voice role, counld be "alloy, echo, fable, onyx, nova, and shimmer"
# https://platform.openai.com/docs/guides/text-to-speech/supported-languages
TTS_VOICE = 'echo'

# voice instructions for vibe
# https://www.openai.fm/
VOICE_INSTRUCTIONS = ""

SOUND_EFFECT_ACTIONS = ["honking", "start engine"]

# car init 
# =================================================================
try:
    my_car = Picarx()
    time.sleep(1)
except Exception as e:
    raise RuntimeError(e)

music = Music()

led = Pin('LED')

DEFAULT_HEAD_PAN = 0
DEFAULT_HEAD_TILT = 20

# Vilib start
# =================================================================
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
# =================================================================
'''
self.energy_threshold = 300  # minimum audio energy to consider for recording
self.dynamic_energy_threshold = True
self.dynamic_energy_adjustment_damping = 0.15
self.dynamic_energy_ratio = 1.5
self.pause_threshold = 0.8  # seconds of non-speaking audio before a phrase is considered complete
self.operation_timeout = None  # seconds after an internal operation (e.g., an API request) starts before it times out, or ``None`` for no timeout

self.phrase_threshold = 0.3  # minimum seconds of speaking audio before we consider the speaking audio a phrase - values below this are ignored (for filtering out clicks and pops)
self.non_speaking_duration = 0.5  # seconds of non-speaking audio to keep on both sides of the recording

'''
recognizer = sr.Recognizer()
recognizer.dynamic_energy_adjustment_damping = 0.16
recognizer.dynamic_energy_ratio = 1.6

# speak_hanlder
# =================================================================
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
# =================================================================
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

    # standby_actions = ['waiting', 'feet_left_right']
    # standby_weights = [1, 0.3]

    action_interval = 5 # seconds
    last_action_time = time.time()
    last_led_time = time.time()

    while True:
        with action_lock:
            _state = action_status

        # led
        # ------------------------------
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
        # ------------------------------
        if _state == 'standby':
            last_action_status = 'standby'
            if time.time() - last_action_time > action_interval:
                # TODO: standby actions
                last_action_time = time.time()
                action_interval = random.randint(2, 6)
        elif _state == 'think':
            if last_action_status != 'think':
                last_action_status = 'think'
                # think(my_car)
                # keep_think(my_car)  # Desactivat: no fer moviment del cap quan pensa
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
# =================================================================
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
            # Comprovar si hi ha una persona detectada
            if Vilib.detect_obj_parameter['human_n'] != 0:
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
# =================================================================
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


# Funcions auxiliars per refactoritzar main()
# =================================================================

def process_voice_input():
    """
    Processa l'entrada de veu: escolta, fa STT i retorna el resultat.
    
    Returns:
        str: Text reconegut, o None si no s'ha pogut processar
    """
    # No resetar càmera si el seguiment visual està actiu
    # El seguiment visual controla els angles de la càmera contínuament
    if not with_img:
        my_car.set_cam_pan_angle(DEFAULT_HEAD_PAN)
        my_car.set_cam_tilt_angle(DEFAULT_HEAD_TILT)

    gray_print("listening ...")

    with action_lock:
        action_status = 'standby'

    _stderr_back = redirect_error_2_null()  # ignore error print to ignore ALSA errors
    # If the chunk_size is set too small (default_size=1024), it may cause the program to freeze
    with sr.Microphone(chunk_size=8192) as source:
        cancel_redirect_error(_stderr_back)  # restore error print
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    # stt
    gray_print('stt ...')
    st = time.time()
    result = openai_helper.stt(audio, language=LANGUAGE)
    gray_print(f"stt takes: {time.time() - st:.3f} s")

    if not result or result == "":
        return None
    
    return result


def process_keyboard_input():
    """
    Processa l'entrada de teclat i retorna el resultat.
    
    Returns:
        str: Text introduït, o None si està buit
    """
    # No resetar càmera si el seguiment visual està actiu
    # El seguiment visual controla els angles de la càmera contínuament
    if not with_img:
        my_car.set_cam_tilt_angle(DEFAULT_HEAD_TILT)

    with action_lock:
        action_status = 'standby'

    result = input(f'\033[1;30m{"input: "}\033[0m').encode(sys.stdin.encoding).decode('utf-8')

    if not result or result == "":
        return None
    
    return result


def get_user_input():
    """
    Obté l'entrada de l'usuari segons el mode configurat (veu o teclat).
    
    Returns:
        str: Text de l'usuari, o None si no s'ha pogut obtenir
    """
    if input_mode == 'voice':
        return process_voice_input()
    elif input_mode == 'keyboard':
        return process_keyboard_input()
    else:
        raise ValueError("Invalid input mode")


def get_gpt_response(user_input):
    """
    Obté la resposta de GPT per a l'entrada de l'usuari.
    
    Args:
        user_input: Text de l'usuari
        
    Returns:
        dict o str: Resposta de GPT
    """
    gray_print(f'thinking ...')
    st = time.time()

    with action_lock:
        action_status = 'think'

    if with_img:
        img_path = os.path.join(current_path, 'img_input.jpg')
        try:
            cv2.imwrite(img_path, Vilib.img)
        except Exception as e:
            print(f'Warning: Could not write image file: {e}')
            # Try alternative location
            img_path = os.path.join(tempfile.gettempdir(), 'img_input.jpg')
            try:
                cv2.imwrite(img_path, Vilib.img)
            except Exception as e2:
                print(f'Warning: Could not write image to temp directory: {e2}')
                # Fallback a diàleg sense imatge
                response = openai_helper.dialogue(user_input)
                gray_print(f'chat takes: {time.time() - st:.3f} s')
                return response
        
        response = openai_helper.dialogue_with_img(user_input, img_path)
    else:
        response = openai_helper.dialogue(user_input)

    gray_print(f'chat takes: {time.time() - st:.3f} s')
    return response


def parse_gpt_response(response):
    """
    Analitza la resposta de GPT i extreu accions i resposta.
    
    Args:
        response: Resposta de GPT (dict o str)
        
    Returns:
        tuple: (actions, answer, sound_actions)
    """
    actions = []
    answer = ''
    sound_actions = []
    
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
                _actions = actions.copy()  # Utilitzar .copy() en lloc de list.copy()
                for _action in _actions:
                    if _action in SOUND_EFFECT_ACTIONS:
                        sound_actions.append(_action)
                        actions.remove(_action)
        else:
            response_str = str(response)
            if len(response_str) > 0:
                actions = []
                answer = response_str

    except Exception as e:
        print(f'Warning: Error processant resposta de GPT: {e}')
        actions = []
        answer = ''
    
    return actions, answer, sound_actions


def execute_tts_and_actions(actions, answer, sound_actions):
    """
    Executa TTS i accions basades en la resposta de GPT.
    
    Args:
        actions: Llista d'accions a executar
        answer: Text per a TTS
        sound_actions: Llista d'efectes de so
    """
    try:
        # ---- tts ----
        tts_status = False
        if answer != '':
            st = time.time()
            _time = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
            tts_f = os.path.join(tts_dir, f"{_time}_raw.wav")
            tts_status = openai_helper.text_to_speech(
                answer, tts_f, TTS_VOICE, 
                response_format='wav', 
                instructions=VOICE_INSTRUCTIONS
            )
            if tts_status:
                global tts_file
                tts_file = os.path.join(tts_dir, f"{_time}_{VOLUME_DB}dB.wav")
                tts_status = sox_volume(tts_f, tts_file, VOLUME_DB)
            gray_print(f'tts takes: {time.time() - st:.3f} s')

        # ---- actions ----
        with action_lock:
            global actions_to_be_done
            actions_to_be_done = actions
            gray_print(f'actions: {actions_to_be_done}')
            action_status = 'actions'

        # --- sound effects and voice ---
        for _sound in sound_actions:
            try:
                sounds_dict[_sound](music)
            except Exception as e:
                print(f'action error: {e}')

        if tts_status:
            global speech_loaded
            with speech_lock:
                speech_loaded = True

        # ---- wait speak done ----
        if tts_status:
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

        print()  # new line

    except Exception as e:
        print(f'actions or TTS error: {e}')


# main
# =================================================================
def main():
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
        # Obté entrada de l'usuari
        user_input = get_user_input()
        if user_input is None:
            print()  # new line
            continue

        # Obté resposta de GPT
        response = get_gpt_response(user_input)

        # Analitza resposta i extreu accions i text
        actions, answer, sound_actions = parse_gpt_response(response)

        # Executa TTS i accions
        execute_tts_and_actions(actions, answer, sound_actions)


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

