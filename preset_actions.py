from time import sleep
import random
from math import sin, cos, pi

import visual_tracking

def wave_hands(car):
    car.reset()
    car.set_cam_tilt_angle(20)
    for _ in range(2):
        car.set_dir_servo_angle(-25)
        sleep(.1)
        # car.set_dir_servo_angle(0)
        # sleep(.1)
        car.set_dir_servo_angle(25)
        sleep(.1)
    car.set_dir_servo_angle(0)

def resist(car):
    car.reset()
    car.set_cam_tilt_angle(10)
    for _ in range(3):
        car.set_dir_servo_angle(-15)
        car.set_cam_pan_angle(15)
        sleep(.1)
        car.set_dir_servo_angle(15)
        car.set_cam_pan_angle(-15)
        sleep(.1)
    car.stop()
    car.set_dir_servo_angle(0)
    car.set_cam_pan_angle(0)

def act_cute(car):
    car.reset()
    car.set_cam_tilt_angle(-20)
    for i in range(15):
        car.forward(5)
        sleep(0.02)
        car.backward(5)
        sleep(0.02)
    car.set_cam_tilt_angle(0)
    car.stop()

def rub_hands(car):
    car.reset()
    for i in range(5):
        car.set_dir_servo_angle(-6)
        sleep(.5)
        car.set_dir_servo_angle(6)
        sleep(.5)
    car.reset()

def think(car):
    car.reset()

    for i in range(11):
        car.set_cam_pan_angle(i*3)
        car.set_cam_tilt_angle(-i*2)
        car.set_dir_servo_angle(i*2)
        sleep(.05)
    sleep(1)
    car.set_cam_pan_angle(15)
    car.set_cam_tilt_angle(-10)
    car.set_dir_servo_angle(10)
    sleep(.1)
    car.reset()

def keep_think(car):
    car.reset()
    for i in range(11):
        car.set_cam_pan_angle(i*3)
        car.set_cam_tilt_angle(-i*2)
        car.set_dir_servo_angle(i*2)
        sleep(.05)

def shake_head(car):
    car.stop()
    car.set_cam_pan_angle(0)
    car.set_cam_pan_angle(60)
    sleep(.2)
    car.set_cam_pan_angle(-50)
    sleep(.1)
    car.set_cam_pan_angle(40)
    sleep(.1)
    car.set_cam_pan_angle(-30)
    sleep(.1)
    car.set_cam_pan_angle(20)
    sleep(.1)
    car.set_cam_pan_angle(-10)
    sleep(.1)
    car.set_cam_pan_angle(10)
    sleep(.1)
    car.set_cam_pan_angle(-5)
    sleep(.1)
    car.set_cam_pan_angle(0)

def nod(car):
    car.reset()
    car.set_cam_tilt_angle(0)
    car.set_cam_tilt_angle(5)
    sleep(.1)
    car.set_cam_tilt_angle(-30)
    sleep(.1)
    car.set_cam_tilt_angle(5)
    sleep(.1)
    car.set_cam_tilt_angle(-30)
    sleep(.1)
    car.set_cam_tilt_angle(0)


def depressed(car):
    # car.reset()
    # car.set_cam_tilt_angle(0)
    # car.set_cam_tilt_angle(20)
    # sleep(.22)
    # car.set_cam_tilt_angle(-30)
    # sleep(.1)
    # car.set_cam_tilt_angle(15)
    # sleep(.1)
    # car.set_cam_tilt_angle(-20)
    # sleep(.1)
    # car.set_cam_tilt_angle(10)
    # sleep(.1)
    # car.set_cam_tilt_angle(-10)
    # sleep(.1)
    # car.set_cam_tilt_angle(5)
    # sleep(.1)
    # car.set_cam_tilt_angle(-5)
    # sleep(.1)
    # car.set_cam_tilt_angle(2)
    # sleep(.1)
    # car.set_cam_tilt_angle(0)

    car.reset()
    car.set_cam_tilt_angle(0)
    car.set_cam_tilt_angle(20)
    sleep(.22)
    car.set_cam_tilt_angle(-22)
    sleep(.1)
    car.set_cam_tilt_angle(10)
    sleep(.1)
    car.set_cam_tilt_angle(-22)
    sleep(.1)
    car.set_cam_tilt_angle(0)
    sleep(.1)
    car.set_cam_tilt_angle(-22)
    sleep(.1)
    car.set_cam_tilt_angle(-10)
    sleep(.1)
    car.set_cam_tilt_angle(-22)
    sleep(.1)
    car.set_cam_tilt_angle(-15)
    sleep(.1)
    car.set_cam_tilt_angle(-22)
    sleep(.1)
    car.set_cam_tilt_angle(-19)
    sleep(.1)
    car.set_cam_tilt_angle(-22)
    sleep(.1)

    sleep(1.5)
    car.reset()

def twist_body(car):
    car.reset()
    for i in range(3):
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        car.set_cam_pan_angle(-20)
        car.set_dir_servo_angle(-10)
        sleep(.1)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        car.set_cam_pan_angle(0)
        car.set_dir_servo_angle(0)
        sleep(.1)
        car.set_motor_speed(1, -20)
        car.set_motor_speed(2, -20)
        car.set_cam_pan_angle(20)
        car.set_dir_servo_angle(10)
        sleep(.1)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        car.set_cam_pan_angle(0)
        car.set_dir_servo_angle(0)

        sleep(.1)


def celebrate(car):
    car.reset()
    car.set_cam_tilt_angle(20)

    car.set_dir_servo_angle(30)
    car.set_cam_pan_angle(60)
    sleep(.3)
    car.set_dir_servo_angle(10)
    car.set_cam_pan_angle(30)
    sleep(.1)
    car.set_dir_servo_angle(30)
    car.set_cam_pan_angle(60)
    sleep(.3)
    car.set_dir_servo_angle(0)
    car.set_cam_pan_angle(0)
    sleep(.2)

    car.set_dir_servo_angle(-30)
    car.set_cam_pan_angle(-60)
    sleep(.3)
    car.set_dir_servo_angle(-10)
    car.set_cam_pan_angle(-30)
    sleep(.1)
    car.set_dir_servo_angle(-30)
    car.set_cam_pan_angle(-60)
    sleep(.3)
    car.set_dir_servo_angle(0)
    car.set_cam_pan_angle(0)
    sleep(.2)

def ballar_sardana(car):
    """Coreografia inspirada en la sardana: balancejos rítmics, passos curts i llargs, ~35 s."""
    car.reset()
    car.set_cam_tilt_angle(15)
    beat = 0.5  # ritme 2/4, ~2 passos/segon
    speed = 25

    # Fase 1: balancejos amb pan/tilt i direcció (passos curts)
    for _ in range(8):
        car.set_dir_servo_angle(-20)
        car.set_cam_pan_angle(-25)
        sleep(beat)
        car.set_dir_servo_angle(20)
        car.set_cam_pan_angle(25)
        sleep(beat)
    car.set_dir_servo_angle(0)
    car.set_cam_pan_angle(0)

    # Fase 2: passos curts endavant-enrere (com passos de sardana)
    for _ in range(4):
        car.forward(speed)
        sleep(beat)
        car.stop()
        sleep(0.1)
        car.backward(speed)
        sleep(beat)
        car.stop()
        sleep(0.1)

    # Fase 3: balancejos més amples (passos llargs)
    for _ in range(8):
        car.set_dir_servo_angle(-30)
        car.set_cam_pan_angle(-40)
        car.set_cam_tilt_angle(10)
        sleep(beat)
        car.set_dir_servo_angle(30)
        car.set_cam_pan_angle(40)
        car.set_cam_tilt_angle(20)
        sleep(beat)
    car.set_dir_servo_angle(0)
    car.set_cam_pan_angle(0)
    car.set_cam_tilt_angle(15)

    # Fase 4: moviment circular suau (girar com en cercle)
    car.set_dir_servo_angle(-25)
    car.forward(speed)
    sleep(2.0)
    car.stop()
    car.set_dir_servo_angle(25)
    car.forward(speed)
    sleep(2.0)
    car.stop()

    car.set_dir_servo_angle(0)
    car.reset()


def sardana(music):
    """Reprodueix música de sardana. Fallback si el fitxer no existeix."""
    import os
    import utils
    path = "sounds/sardana.wav"
    if not os.path.isfile(path):
        utils.warn(f"Fitxer {path} no trobat. Afegeix música de sardana per escoltar-la.")
        return
    try:
        music.sound_play_threading(path, 80)
    except Exception as e:
        utils.warn(f"No s'ha pogut reproduir {path}: {e}")


def honking(music):
    import utils
    music.sound_play_threading("sounds/car-double-horn.wav", 100)

def start_engine(music):
    import utils
    music.sound_play_threading("sounds/car-start-engine.wav", 50)

def advance_20cm(car):
    """Avança el cotxe aproximadament 20 cm endavant"""
    car.reset()
    car.set_dir_servo_angle(0)  # Assegurar que va recte
    car.forward(30)  # Velocitat moderada
    sleep(0.8)  # Temps per avançar aproximadament 20 cm
    car.stop()


def donar_la_volta(car):
    """Donar la volta: engeu enrere cap a l'esquerra (rodes a l'esquerra), després avanci cap a la dreta (rodes a la dreta). Adequat per tracció només a les rodes motrius. Durada triplicada per girar ~180°."""
    car.reset()
    car.set_dir_servo_angle(0)
    sleep(0.05)
    speed = 45
    turn_duration = 2.7  # Triple de 0.9 s per fer un gir molt més ample
    # 1) Enrera amb les rodes cap a l'esquerra
    car.set_dir_servo_angle(-40)
    sleep(0.08)
    car.backward(speed)
    sleep(turn_duration)
    car.stop()
    sleep(0.05)
    # 2) Endavant amb les rodes cap a la dreta
    car.set_dir_servo_angle(40)
    sleep(0.08)
    car.forward(speed)
    sleep(turn_duration)
    car.stop()
    car.set_dir_servo_angle(0)
    car.reset()


def seguir_persona(car):
    """Inicia el seguiment visual via el mòdul visual_tracking (pan/tilt i moviment reactiu)."""
    visual_tracking.start_visual_tracking()


def aturar_seguiment(car):
    """Atura el seguiment visual via el mòdul visual_tracking."""
    visual_tracking.stop_visual_tracking()


actions_dict = {
    "shake head":shake_head, 
    "nod": nod,
    "wave hands": wave_hands,
    "resist": resist,
    "act cute": act_cute,
    "rub hands": rub_hands,
    "think": think,
    "twist body": twist_body,
    "celebrate": celebrate,
    "depressed": depressed,
    "advance": advance_20cm,
    "avanci": advance_20cm,
    "forward 20cm": advance_20cm,
    "donar la volta": donar_la_volta,
    "girar": donar_la_volta,
    "turn around": donar_la_volta,
    "turn arround": donar_la_volta,  # typo alias (LLM sometimes returns this)
    "seguir persona": seguir_persona,
    "follow me": seguir_persona,
    "follow": seguir_persona,
    "aturar seguiment": aturar_seguiment,
    "stop following": aturar_seguiment,
    "stop follow": aturar_seguiment,
    "ballar sardana": ballar_sardana,
    "ballar una sardana": ballar_sardana,
}

sounds_dict = {
    "honking": honking,
    "start engine": start_engine,
    "sardana": sardana,
    "cantar sardana": sardana,
}


if __name__ == "__main__":
    from picarx import Picarx
    from robot_hat import Music
    import os

    os.popen("pinctrl set 20 op dh") # enable robot_hat speake switch
    current_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_path) # change working directory

    my_car = Picarx()
    my_car.reset()

    music = Music()

    sleep(.5)

    _actions_num = len(actions_dict)
    actions = list(actions_dict.keys())
    for i, key in enumerate(actions_dict):
        print(f'{i} {key}')
    
    _sounds_num = len(sounds_dict)
    sounds = list(sounds_dict.keys())
    for i, key in enumerate(sounds_dict):
        print(f'{_actions_num+i} {key}')

    last_key = None

    try:
        while True:
            key = input()

            if key == '':
                if last_key > _actions_num - 1:
                    print(sounds[last_key-_actions_num])
                    sounds_dict[sounds[last_key-_actions_num]](music)
                else:
                    print(actions[last_key])
                    actions_dict[actions[last_key]](my_car)
            else:
                key = int(key)
                if key > (_actions_num + _sounds_num - 1):
                    print("Invalid key")
                elif key > (_actions_num - 1):
                    last_key = key
                    print(sounds[last_key-_actions_num])
                    sounds_dict[sounds[last_key-_actions_num]](music)
                else:
                    last_key = key
                    print(actions[key])
                    actions_dict[actions[key]](my_car)

            # sleep(2)
            # shake_head(my_car)
            # nod(my_car)
            # wave_hands(my_car)
            # resist(my_car)
            # act_cute(my_car)
            # rub_hands(my_car)
            # think(my_car)
            # twist(my_car)
            # celebrate(my_car)
            # depressed(my_car)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error:\n {e}')
    finally:
        my_car.reset()
        sleep(.1)




