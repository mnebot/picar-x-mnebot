"""
Mòdul de seguiment visual per al picar-x
Implementa seguiment visual pur amb càmera (pan/tilt) amb filtre de suavització
i detecció de persona centrada (FASE 1, PAS 3)
"""

import time
import threading


def clamp_number(num, a, b):
    """Limita un número entre a i b"""
    return max(min(num, max(a, b)), min(a, b))


def create_visual_tracking_handler(car, vilib, with_img, default_head_tilt):
    """
    Crea i retorna el handler de seguiment visual amb detecció de persona centrada
    
    Args:
        car: Instància de Picarx
        vilib: Mòdul Vilib (o None si no hi ha imatge)
        with_img: Boolean indicant si hi ha imatge disponible
        default_head_tilt: Angle per defecte del tilt de la càmera
    
    Returns:
        Tupla (handler_function, state_dict, lock, is_person_centered_func) on:
        - handler_function: Funció handler que es pot executar en un thread
        - state_dict: Diccionari amb l'estat (centered: bool)
        - lock: Lock per accedir a l'estat de forma thread-safe
        - is_person_centered_func: Funció per consultar si la persona està centrada
    """
    
    # Estat compartit
    state = {'centered': False}
    state_lock = threading.Lock()
    
    def visual_tracking_handler():
        """Fil que fa seguiment visual pur amb la càmera (pan/tilt) amb filtre de suavització"""
        
        if not with_img or vilib is None:
            return
        
        # Esperar una mica per assegurar que Vilib està completament inicialitzat
        time.sleep(1.0)
        
        # Configuració de zona central (FASE 1, PAS 3)
        CAMERA_WIDTH = 640
        CAMERA_HEIGHT = 480
        CAMERA_CENTER_X = CAMERA_WIDTH / 2
        CAMERA_CENTER_Y = CAMERA_HEIGHT / 2
        CENTER_ZONE_TOLERANCE = 30  # ±30 píxels del centre
        
        # Configuració del filtre de suavització
        DETECTION_HISTORY_SIZE = 5  # Mantenir últimes 5 deteccions
        MAX_ANGLE_CHANGE_PER_ITERATION = 3  # Graus màxims de canvi per iteració
        
        # Històric de deteccions per mitjana mòbil
        detection_history = {
            'x': [],
            'y': []
        }
        
        # Pesos per mitjana ponderada (més pes a deteccions recents)
        weights = [0.1, 0.15, 0.2, 0.25, 0.3]
        
        # Angles actuals de la càmera
        x_angle = 0
        y_angle = default_head_tilt
        
        while True:
            try:
                # Comprovar si hi ha una persona detectada
                if vilib.detect_obj_parameter.get('human_n', 0) != 0:
                    coordinate_x = vilib.detect_obj_parameter['human_x']
                    coordinate_y = vilib.detect_obj_parameter['human_y']
                    
                    # Afegir a l'històric
                    detection_history['x'].append(coordinate_x)
                    detection_history['y'].append(coordinate_y)
                    
                    # Mantenir només últimes N deteccions
                    if len(detection_history['x']) > DETECTION_HISTORY_SIZE:
                        detection_history['x'].pop(0)
                        detection_history['y'].pop(0)
                    
                    # Calcular mitjana ponderada (més pes a valors recents)
                    if len(detection_history['x']) >= 2:
                        # Utilitzar només els pesos necessaris
                        current_weights = weights[-len(detection_history['x']):]
                        weight_sum = sum(current_weights)
                        
                        smoothed_x = sum(x * w for x, w in zip(detection_history['x'], current_weights)) / weight_sum
                        smoothed_y = sum(y * w for y, w in zip(detection_history['y'], current_weights)) / weight_sum
                    else:
                        # Si només hi ha una detecció, usar-la directament
                        smoothed_x = coordinate_x
                        smoothed_y = coordinate_y
                    
                    # Calcular desplaçament respecte al centre (FASE 1, PAS 3)
                    offset_x = smoothed_x - CAMERA_CENTER_X
                    offset_y = smoothed_y - CAMERA_CENTER_Y
                    
                    # Detectar si està centrada (FASE 1, PAS 3)
                    is_centered = abs(offset_x) < CENTER_ZONE_TOLERANCE and abs(offset_y) < CENTER_ZONE_TOLERANCE
                    
                    # Actualitzar estat global
                    with state_lock:
                        state['centered'] = is_centered
                    
                    # Calcular canvi d'angle desitjat
                    desired_x_change = (smoothed_x * 10 / 640) - 5
                    desired_y_change = -((smoothed_y * 10 / 480) - 5)  # Negatiu per tilt
                    
                    # Limitar velocitat de canvi d'angle
                    actual_x_change = clamp_number(desired_x_change, -MAX_ANGLE_CHANGE_PER_ITERATION, MAX_ANGLE_CHANGE_PER_ITERATION)
                    actual_y_change = clamp_number(desired_y_change, -MAX_ANGLE_CHANGE_PER_ITERATION, MAX_ANGLE_CHANGE_PER_ITERATION)
                    
                    # Aplicar canvi limitat
                    x_angle += actual_x_change
                    x_angle = clamp_number(x_angle, -35, 35)
                    car.set_cam_pan_angle(x_angle)
                    
                    y_angle += actual_y_change
                    y_angle = clamp_number(y_angle, -35, 35)
                    car.set_cam_tilt_angle(y_angle)
                else:
                    # Si no hi ha detecció, buidar l'històric i actualitzar estat
                    detection_history['x'].clear()
                    detection_history['y'].clear()
                    with state_lock:
                        state['centered'] = False
                
                time.sleep(0.05)
                
            except Exception as e:
                print(f'[Visual Tracking] Error: {e}')
                time.sleep(0.1)
    
    def is_person_centered():
        """Retorna True si la persona detectada està centrada a la imatge"""
        with state_lock:
            return state['centered']
    
    return visual_tracking_handler, state, state_lock, is_person_centered

