"""
Mòdul de seguiment visual per al picar-x
Implementa seguiment visual pur amb càmera (pan/tilt) amb filtre de suavització
i detecció de persona centrada (FASE 1, PAS 3)
"""

import time
import threading


# Constants de configuració
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_CENTER_X = CAMERA_WIDTH / 2
CAMERA_CENTER_Y = CAMERA_HEIGHT / 2
CENTER_ZONE_TOLERANCE = 30  # ±30 píxels del centre per considerar la persona centrada

DETECTION_HISTORY_SIZE = 5  # Nombre de deteccions a mantenir per al filtre de suavització
MAX_ANGLE_CHANGE_PER_ITERATION = 3  # Graus màxims de canvi d'angle per iteració
CAMERA_PAN_MIN_ANGLE = -35  # Angle mínim de pan de la càmera
CAMERA_PAN_MAX_ANGLE = 35   # Angle màxim de pan de la càmera
CAMERA_TILT_MIN_ANGLE = -35  # Angle mínim de tilt de la càmera
CAMERA_TILT_MAX_ANGLE = 35   # Angle màxim de tilt de la càmera

# Pesos per mitjana ponderada (més pes a deteccions recents)
SMOOTHING_WEIGHTS = [0.1, 0.15, 0.2, 0.25, 0.3]

# Constants de temps
VILIB_INIT_DELAY = 1.0  # Segons d'espera per assegurar que Vilib està inicialitzat
TRACKING_LOOP_DELAY = 0.05  # Segons entre iteracions del seguiment
ERROR_RETRY_DELAY = 0.1  # Segons d'espera després d'un error


def clamp_number(num, a, b):
    """
    Limita un número entre dos valors (inclusius).
    
    Args:
        num: Número a limitar
        a: Primer límit
        b: Segon límit
    
    Returns:
        Número limitat entre a i b
    """
    return max(min(num, max(a, b)), min(a, b))


def calcular_mitjana_ponderada(valors, pesos):
    """
    Calcula la mitjana ponderada d'una llista de valors.
    
    Args:
        valors: Llista de valors numèrics
        pesos: Llista de pesos (ha de tenir la mateixa longitud que valors)
    
    Returns:
        Mitjana ponderada dels valors
    """
    if not valors:
        return 0.0
    
    if len(valors) == 1:
        return float(valors[0])
    
    # Utilitzar només els pesos necessaris
    pesos_actuals = pesos[-len(valors):]
    suma_pesos = sum(pesos_actuals)
    
    if suma_pesos == 0:
        return float(valors[-1]) if valors else 0.0
    
    return sum(v * p for v, p in zip(valors, pesos_actuals)) / suma_pesos


def calcular_canvi_angle(coordenada, dimensio_camera, invertir=False):
    """
    Calcula el canvi d'angle necessari per centrar la coordenada.
    
    Args:
        coordenada: Coordenada de la persona (x o y)
        dimensio_camera: Dimensió de la càmera (amplada o alçada)
        invertir: Si és True, inverteix el signe del canvi (per tilt)
    
    Returns:
        Canvi d'angle desitjat en graus
    
    Raises:
        ValueError: Si dimensio_camera és zero o negativa
    """
    # Validar que dimensio_camera sigui vàlida per evitar divisió per zero
    if not isinstance(dimensio_camera, (int, float)) or dimensio_camera <= 0:
        raise ValueError(f"dimensio_camera ha de ser un número positiu, rebut: {dimensio_camera}")
    
    # Validar que coordenada sigui un número
    if not isinstance(coordenada, (int, float)):
        raise ValueError(f"coordenada ha de ser un número, rebut: {coordenada}")
    
    canvi = (coordenada * 10 / dimensio_camera) - 5
    return -canvi if invertir else canvi


def processar_deteccio_persona(vilib, detection_history, state, state_lock):
    """
    Processa una detecció de persona i actualitza l'estat.
    
    Args:
        vilib: Mòdul Vilib amb deteccions
        detection_history: Diccionari amb històric de deteccions {'x': [], 'y': []}
        state: Diccionari amb l'estat compartit
        state_lock: Lock per accedir a l'estat de forma thread-safe
    
    Returns:
        Tupla (posicio_suavitzada_x, posicio_suavitzada_y, esta_centrada) o None si no hi ha detecció vàlida
    """
    # Comprovar si hi ha una persona detectada
    if not hasattr(vilib, 'detect_obj_parameter') or not isinstance(vilib.detect_obj_parameter, dict):
        return None
    
    num_persones = vilib.detect_obj_parameter.get('human_n', 0)
    if num_persones == 0:
        return None
    
    # Obtenir coordenades de la persona detectada
    coordenada_x = vilib.detect_obj_parameter.get('human_x', CAMERA_CENTER_X)
    coordenada_y = vilib.detect_obj_parameter.get('human_y', CAMERA_CENTER_Y)
    
    # Validar que les coordenades siguin vàlides (dins del rang de la càmera)
    coordenada_x = clamp_number(coordenada_x, 0, CAMERA_WIDTH)
    coordenada_y = clamp_number(coordenada_y, 0, CAMERA_HEIGHT)
    
    # Afegir a l'històric de deteccions
    detection_history['x'].append(coordenada_x)
    detection_history['y'].append(coordenada_y)
    
    # Mantenir només últimes N deteccions
    if len(detection_history['x']) > DETECTION_HISTORY_SIZE:
        detection_history['x'].pop(0)
        detection_history['y'].pop(0)
    
    # Calcular posició suavitzada mitjançant mitjana ponderada
    posicio_suavitzada_x = calcular_mitjana_ponderada(
        detection_history['x'],
        SMOOTHING_WEIGHTS
    )
    posicio_suavitzada_y = calcular_mitjana_ponderada(
        detection_history['y'],
        SMOOTHING_WEIGHTS
    )
    
    # Calcular desplaçament respecte al centre de la imatge
    desplacament_x = posicio_suavitzada_x - CAMERA_CENTER_X
    desplacament_y = posicio_suavitzada_y - CAMERA_CENTER_Y
    
    # Detectar si la persona està centrada dins de la zona de tolerància
    esta_centrada = (
        abs(desplacament_x) < CENTER_ZONE_TOLERANCE and
        abs(desplacament_y) < CENTER_ZONE_TOLERANCE
    )
    
    # Actualitzar estat global de forma thread-safe
    with state_lock:
        state['centered'] = esta_centrada
    
    return (posicio_suavitzada_x, posicio_suavitzada_y, esta_centrada)


def aplicar_angles_camera(car, pan_angle, tilt_angle):
    """
    Aplica els angles de pan i tilt a la càmera amb validació.
    
    Args:
        car: Instància de Picarx
        pan_angle: Angle de pan
        tilt_angle: Angle de tilt
    
    Returns:
        True si s'han aplicat correctament, False si hi ha hagut un error
    """
    try:
        if hasattr(car, 'set_cam_pan_angle'):
            car.set_cam_pan_angle(pan_angle)
        if hasattr(car, 'set_cam_tilt_angle'):
            car.set_cam_tilt_angle(tilt_angle)
        return True
    except (AttributeError, Exception) as e:
        # Si hi ha un error amb la càmera, registrar però continuar
        print(f'[Visual Tracking] Error actualitzant angles de càmera: {e}')
        return False


def processar_iteracio_tracking(vilib, detection_history, state, state_lock, 
                                 car, pan_angle, tilt_angle):
    """
    Processa una iteració del loop de seguiment visual.
    
    Args:
        vilib: Mòdul Vilib amb deteccions
        detection_history: Diccionari amb històric de deteccions
        state: Diccionari amb l'estat compartit
        state_lock: Lock per accedir a l'estat
        car: Instància de Picarx
        pan_angle: Angle actual de pan
        tilt_angle: Angle actual de tilt
    
    Returns:
        Tupla (nou_pan_angle, nou_tilt_angle) amb els nous angles
    """
    # Processar detecció de persona
    resultat = processar_deteccio_persona(vilib, detection_history, state, state_lock)
    
    if resultat is not None:
        posicio_suavitzada_x, posicio_suavitzada_y, _ = resultat
        
        # Calcular canvis d'angle desitjats per centrar la persona
        canvi_pan_desitjat = calcular_canvi_angle(
            posicio_suavitzada_x,
            CAMERA_WIDTH,
            invertir=False
        )
        canvi_tilt_desitjat = calcular_canvi_angle(
            posicio_suavitzada_y,
            CAMERA_HEIGHT,
            invertir=True
        )
        
        # Actualitzar angles de la càmera amb limitació de velocitat
        nou_pan_angle = actualitzar_angle_camera(
            pan_angle,
            canvi_pan_desitjat,
            CAMERA_PAN_MIN_ANGLE,
            CAMERA_PAN_MAX_ANGLE
        )
        nou_tilt_angle = actualitzar_angle_camera(
            tilt_angle,
            canvi_tilt_desitjat,
            CAMERA_TILT_MIN_ANGLE,
            CAMERA_TILT_MAX_ANGLE
        )
        
        # Aplicar els nous angles a la càmera amb validació
        aplicar_angles_camera(car, nou_pan_angle, nou_tilt_angle)
        
        return (nou_pan_angle, nou_tilt_angle)
    else:
        # Si no hi ha detecció, buidar l'històric i actualitzar estat
        detection_history['x'].clear()
        detection_history['y'].clear()
        with state_lock:
            state['centered'] = False
        
        return (pan_angle, tilt_angle)


def actualitzar_angle_camera(angle_actual, canvi_desitjat, angle_min, angle_max):
    """
    Actualitza l'angle de la càmera aplicant un canvi limitat.
    
    Args:
        angle_actual: Angle actual de la càmera
        canvi_desitjat: Canvi d'angle desitjat
        angle_min: Angle mínim permès
        angle_max: Angle màxim permès
    
    Returns:
        Nou angle de la càmera (limitada dins del rang permès)
    """
    # Limitar velocitat de canvi d'angle
    canvi_limit = clamp_number(
        canvi_desitjat,
        -MAX_ANGLE_CHANGE_PER_ITERATION,
        MAX_ANGLE_CHANGE_PER_ITERATION
    )
    
    # Aplicar canvi i limitar dins del rang permès
    nou_angle = angle_actual + canvi_limit
    return clamp_number(nou_angle, angle_min, angle_max)


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
    
    Raises:
        ValueError: Si els paràmetres no són vàlids
    """
    
    # Validar paràmetres d'entrada
    if car is None:
        raise ValueError("car no pot ser None")
    
    if not isinstance(with_img, bool):
        raise ValueError("with_img ha de ser un boolean")
    
    if not isinstance(default_head_tilt, (int, float)):
        raise ValueError("default_head_tilt ha de ser un número")
    
    # Validar que default_head_tilt estigui dins del rang permès
    default_head_tilt = clamp_number(
        default_head_tilt,
        CAMERA_TILT_MIN_ANGLE,
        CAMERA_TILT_MAX_ANGLE
    )
    
    # Estat compartit
    state = {'centered': False}
    state_lock = threading.Lock()
    
    def visual_tracking_handler():
        """
        Fil que fa seguiment visual pur amb la càmera (pan/tilt) amb filtre de suavització.
        
        Aquest handler executa un loop continu que:
        - Detecta persones utilitzant Vilib
        - Aplica un filtre de suavització a les deteccions
        - Calcula i aplica canvis d'angle de càmera per centrar la persona
        - Detecta quan la persona està centrada a la imatge
        """
        
        if not with_img or vilib is None:
            return
        
        # Esperar una mica per assegurar que Vilib està completament inicialitzat
        time.sleep(VILIB_INIT_DELAY)
        
        # Històric de deteccions per mitjana mòbil
        detection_history = {
            'x': [],
            'y': []
        }
        
        # Angles actuals de la càmera
        pan_angle = 0
        tilt_angle = default_head_tilt
        
        while True:
            try:
                pan_angle, tilt_angle = processar_iteracio_tracking(
                    vilib, detection_history, state, state_lock,
                    car, pan_angle, tilt_angle
                )
                time.sleep(TRACKING_LOOP_DELAY)
                
            except Exception as e:
                print(f'[Visual Tracking] Error: {e}')
                time.sleep(ERROR_RETRY_DELAY)
    
    def is_person_centered():
        """
        Consulta si la persona detectada està centrada a la imatge.
        
        Returns:
            True si la persona està centrada dins de la zona de tolerància,
            False en cas contrari
        """
        with state_lock:
            return state['centered']
    
    return visual_tracking_handler, state, state_lock, is_person_centered

