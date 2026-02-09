"""
Mòdul de seguiment visual per al picar-x
Implementa seguiment visual pur amb càmera (pan/tilt) amb filtre de suavització,
detecció de persona centrada (FASE 1), moviment reactiu quan surt del camp de
visió (FASE 2.1) i estratègia de recerca (FASE 2.2).
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
PERSON_LOST_TIMEOUT = 0.5  # Segons sense detecció per considerar persona perduda (FASE 2.1)

# Constants per moviment reactiu (FASE 2.1)
TURN_ANGLE_DEGREES = 30  # Graus de gir de les rodes cap a la direcció de la persona
TURN_DURATION = 0.4  # Segons de durada del gir
TURN_SPEED = 25  # Velocitat durant el gir (0-100)

# Constants per estratègia de recerca (FASE 2.2)
SEARCH_TIMEOUT = 5.0  # Segons màxims de recerca abans de desistir
SEARCH_EXTRA_TURN_INTERVAL = 1.0  # Segons entre girs addicionals
SEARCH_EXTRA_TURN_ANGLE = 15  # Graus addicionals per gir durant recerca
SEARCH_CAMERA_PAN_STEP = 8  # Graus de pan per pas de recerca amb càmera
SEARCH_CAMERA_STEP_INTERVAL = 0.25  # Segons entre passos de recerca amb càmera

# Estat del mòdul per start/stop (assignat quan es crida create_visual_tracking_handler)
_tracking_ref = {}


def start_visual_tracking():
    """
    Inicia el thread de seguiment visual.
    Si el handler encara no s'ha creat (no s'ha cridat create_visual_tracking_handler), no fa res.
    """
    if not _tracking_ref:
        return
    handler = _tracking_ref.get('handler')
    state = _tracking_ref.get('state')
    lock = _tracking_ref.get('lock')
    thread_ref = _tracking_ref.get('thread_ref')
    if handler is None or state is None or lock is None or thread_ref is None:
        return
    with lock:
        state['stop_requested'] = False
    t = thread_ref.get('thread')
    if t is None or not t.is_alive():
        t = threading.Thread(target=handler)
        t.daemon = True
        thread_ref['thread'] = t
        t.start()


def stop_visual_tracking():
    """
    Atura el thread de seguiment visual (posa stop_requested a True).
    Si el handler encara no s'ha creat, no fa res.
    """
    if not _tracking_ref:
        return
    state = _tracking_ref.get('state')
    lock = _tracking_ref.get('lock')
    if state is None or lock is None:
        return
    with lock:
        state['stop_requested'] = True


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
    
    # Actualitzar estat global de forma thread-safe (incloent última posició per FASE 2.1)
    with state_lock:
        state['centered'] = esta_centrada
        state['last_seen_x'] = posicio_suavitzada_x
        state['last_seen_time'] = time.time()
        state['person_lost_turn_done'] = False  # Reset quan tornem a detectar
    
    return (posicio_suavitzada_x, posicio_suavitzada_y, esta_centrada)


def girar_robot_cap_direccio(car, direccio, graus=None):
    """
    Gira el robot cap a la direcció indicada (esquerra o dreta).
    
    Útil quan la persona surt del camp de visió: el robot gira cap allà on
    es va la persona segons l'última posició coneguda (FASE 2.1).
    Per l'estratègia de recerca (FASE 2.2) es poden especificar girs més curts.
    
    Args:
        car: Instància de Picarx
        direccio: 'esquerra' o 'dreta'
        graus: Angle de gir en graus (None = TURN_ANGLE_DEGREES per defecte)
    
    Returns:
        True si el gir s'ha executat, False si hi ha hagut error
    """
    try:
        if not hasattr(car, 'set_dir_servo_angle') or not hasattr(car, 'forward') or not hasattr(car, 'stop'):
            return False
        
        angle_graus = graus if graus is not None else TURN_ANGLE_DEGREES
        angle = -angle_graus if direccio == 'esquerra' else angle_graus
        car.set_dir_servo_angle(angle)
        car.forward(clamp_number(TURN_SPEED, 0, 100))
        time.sleep(TURN_DURATION)
        car.stop()
        car.set_dir_servo_angle(0)
        return True
    except (AttributeError, Exception) as e:
        print(f'[Visual Tracking] Error en gir reactiu: {e}')
        try:
            car.stop()
            if hasattr(car, 'set_dir_servo_angle'):
                car.set_dir_servo_angle(0)
        except Exception:
            pass
        return False


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
        # Persona trobada: sortir del mode recerca si hi érem (FASE 2.2)
        with state_lock:
            if state.get('search_start_time') is not None:
                state['search_start_time'] = None
                state['search_direction'] = None
                state['search_last_extra_turn_time'] = None
                state['search_last_camera_step_time'] = None
        
        posicio_suavitzada_x, posicio_suavitzada_y, _ = resultat
        
        # Calcular i actualitzar angles de la càmera (elimina duplicació pan/tilt)
        nou_pan_angle = calcular_i_actualitzar_angle(
            posicio_suavitzada_x, CAMERA_WIDTH, pan_angle,
            CAMERA_PAN_MIN_ANGLE, CAMERA_PAN_MAX_ANGLE, invertir=False
        )
        nou_tilt_angle = calcular_i_actualitzar_angle(
            posicio_suavitzada_y, CAMERA_HEIGHT, tilt_angle,
            CAMERA_TILT_MIN_ANGLE, CAMERA_TILT_MAX_ANGLE, invertir=True
        )
        
        # Aplicar els nous angles a la càmera amb validació
        aplicar_angles_camera(car, nou_pan_angle, nou_tilt_angle)
        
        return (nou_pan_angle, nou_tilt_angle)
    else:
        # Si no hi ha detecció: buidar històric, actualitzar estat i recerca (FASE 2.1 + 2.2)
        detection_history['x'].clear()
        detection_history['y'].clear()
        
        current_time = time.time()
        with state_lock:
            state['centered'] = False
            last_seen_x = state.get('last_seen_x')
            last_seen_time = state.get('last_seen_time')
            turn_done = state.get('person_lost_turn_done', False)
            search_start = state.get('search_start_time')
            search_dir = state.get('search_direction')
            search_last_turn = state.get('search_last_extra_turn_time')
            search_last_cam = state.get('search_last_camera_step_time')
            search_pan_dir = state.get('search_pan_direction', 1)
        
        # Mode recerca actiu (FASE 2.2): buscar amb càmera i girs addicionals
        if search_start is not None:
            elapsed = current_time - search_start
            if elapsed >= SEARCH_TIMEOUT:
                # Timeout: sortir del mode recerca
                with state_lock:
                    state['search_start_time'] = None
                    state['search_direction'] = None
                    state['search_last_extra_turn_time'] = None
                    state['search_last_camera_step_time'] = None
                return (pan_angle, tilt_angle)
            
            # Gir addicional periòdic (cada SEARCH_EXTRA_TURN_INTERVAL)
            last_turn = search_last_turn if search_last_turn is not None else search_start
            if (current_time - last_turn) >= SEARCH_EXTRA_TURN_INTERVAL and search_dir:
                if girar_robot_cap_direccio(car, search_dir, SEARCH_EXTRA_TURN_ANGLE):
                    with state_lock:
                        state['search_last_extra_turn_time'] = current_time
            
            # Recerca amb càmera: moure pan periòdicament
            last_cam = search_last_cam if search_last_cam is not None else search_start
            if (current_time - last_cam) >= SEARCH_CAMERA_STEP_INTERVAL:
                nou_pan = pan_angle + SEARCH_CAMERA_PAN_STEP * search_pan_dir
                nou_pan = clamp_number(nou_pan, CAMERA_PAN_MIN_ANGLE, CAMERA_PAN_MAX_ANGLE)
                # Invertir sentit si arribem als límits
                if nou_pan >= CAMERA_PAN_MAX_ANGLE or nou_pan <= CAMERA_PAN_MIN_ANGLE:
                    search_pan_dir = -search_pan_dir
                    with state_lock:
                        state['search_pan_direction'] = search_pan_dir
                aplicar_angles_camera(car, nou_pan, tilt_angle)
                with state_lock:
                    state['search_last_camera_step_time'] = current_time
                return (nou_pan, tilt_angle)
            
            return (pan_angle, tilt_angle)
        
        # Detectar persona perduda: sense detecció durant PERSON_LOST_TIMEOUT (FASE 2.1)
        if (last_seen_time is not None and
                not turn_done and
                (current_time - last_seen_time) >= PERSON_LOST_TIMEOUT):
            # Determinar direcció segons última posició (esquerra/dreta del centre)
            if last_seen_x is not None:
                direccio = 'esquerra' if last_seen_x < CAMERA_CENTER_X else 'dreta'
                if girar_robot_cap_direccio(car, direccio):
                    with state_lock:
                        state['person_lost_turn_done'] = True
                        state['last_seen_time'] = current_time  # Cooldown
                        # Iniciar mode recerca (FASE 2.2)
                        state['search_start_time'] = current_time
                        state['search_direction'] = direccio
                        state['search_last_extra_turn_time'] = current_time
                        state['search_last_camera_step_time'] = current_time
                        # Sentit de recerca amb càmera: cap a on va la persona
                        state['search_pan_direction'] = -1 if direccio == 'esquerra' else 1
        
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


def calcular_i_actualitzar_angle(posicio, dimensio_camera, angle_actual, 
                                   angle_min, angle_max, invertir=False):
    """
    Calcula el canvi d'angle necessari per centrar la posició i actualitza l'angle de la càmera.
    
    Aquesta funció elimina la duplicació de codi en els càlculs de pan i tilt.
    
    Args:
        posicio: Posició de la persona (x o y) en píxels
        dimensio_camera: Dimensió de la càmera (amplada o alçada)
        angle_actual: Angle actual de la càmera
        angle_min: Angle mínim permès
        angle_max: Angle màxim permès
        invertir: Si és True, inverteix el signe del canvi (per tilt)
    
    Returns:
        Nou angle de la càmera (limitada dins del rang permès)
    """
    canvi_desitjat = calcular_canvi_angle(posicio, dimensio_camera, invertir)
    return actualitzar_angle_camera(angle_actual, canvi_desitjat, angle_min, angle_max)


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
    
    # Estat compartit (FASE 2.1: persona perduda, FASE 2.2: estratègia de recerca)
    # stop_requested: quan és True, el loop del handler acaba (per aturar seguiment des d'una acció)
    state = {
        'centered': False,
        'last_seen_x': None,
        'last_seen_time': None,
        'person_lost_turn_done': False,
        # FASE 2.2: mode recerca
        'search_start_time': None,
        'search_direction': None,
        'search_last_extra_turn_time': None,
        'search_last_camera_step_time': None,
        'search_pan_direction': 1,  # 1 o -1 per sentit de l'escombrat
        'stop_requested': False,
    }
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
            with state_lock:
                if state.get('stop_requested'):
                    break
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
    
    # Emmagatzemar referències per start_visual_tracking() i stop_visual_tracking()
    _tracking_ref['handler'] = visual_tracking_handler
    _tracking_ref['state'] = state
    _tracking_ref['lock'] = state_lock
    _tracking_ref['thread_ref'] = {'thread': None}
    
    return visual_tracking_handler, state, state_lock, is_person_centered

