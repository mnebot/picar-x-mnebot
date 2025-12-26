from picarx import Picarx
from time import sleep
from vilib import Vilib
from robot_hat import TTS
from os import geteuid

if geteuid() != 0:
    print(f"\033[0;33m{'The program needs to be run using sudo, otherwise there may be no sound.'}\033[0m")

px = Picarx()
tts = TTS()
tts.lang("en-US")

# Track if we've already greeted someone to avoid repeating
person_detected = False
greeting_cooldown = 0  # Cooldown timer to prevent repeated greetings

def main():
    global person_detected, greeting_cooldown
    
    print("Starting camera and person detection...")
    print("The picar-x will say 'Hello' when it sees someone!")
    print("Press Ctrl+C to exit.\n")
    
    # Start camera and enable human detection
    Vilib.camera_start()
    Vilib.display()
    Vilib.face_detect_switch(True)
    
    while True:
        # Check if a person is detected
        if Vilib.detect_obj_parameter['human_n'] != 0:
            # Person detected
            if not person_detected:
                # New person detected - greet them!
                print("Person detected! Saying hello...")
                tts.say("Hello")
                person_detected = True
                greeting_cooldown = 0
            else:
                # Person still there, just update cooldown
                greeting_cooldown = 0
        else:
            # No person detected
            if person_detected:
                # Person left - reset for next detection
                person_detected = False
                greeting_cooldown = 0
            else:
                # No person, increment cooldown
                greeting_cooldown += 1
        
        sleep(0.1)  # Small delay to avoid excessive checking


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        px.stop()
        print("Stopped and exited")

