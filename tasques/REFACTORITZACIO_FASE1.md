# PROPOSTES DE REFACTORITZACIÓ - FASE 1

Aquest document proposa diferents tasques de refactorització per millorar la qualitat del codi de la FASE 1.

---

## TASCA 1: Extreure constants de càmera a configuració agrupada

**Prioritat**: Mitjana  
**Esforç**: Baix  
**Impacte**: Mantenibilitat

### Descripció
Agrupar les constants relacionades amb la càmera en una estructura més clara.

### Codi actual
```python
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_CENTER_X = CAMERA_WIDTH / 2
CAMERA_CENTER_Y = CAMERA_HEIGHT / 2
CENTER_ZONE_TOLERANCE = 30
CAMERA_PAN_MIN_ANGLE = -35
CAMERA_PAN_MAX_ANGLE = 35
CAMERA_TILT_MIN_ANGLE = -35
CAMERA_TILT_MAX_ANGLE = 35
```

### Proposta
```python
# Configuració de càmera
CAMERA_CONFIG = {
    'width': 640,
    'height': 480,
    'center_tolerance': 30,
    'pan_range': (-35, 35),
    'tilt_range': (-35, 35)
}

CAMERA_CENTER_X = CAMERA_CONFIG['width'] / 2
CAMERA_CENTER_Y = CAMERA_CONFIG['height'] / 2
CAMERA_PAN_MIN_ANGLE, CAMERA_PAN_MAX_ANGLE = CAMERA_CONFIG['pan_range']
CAMERA_TILT_MIN_ANGLE, CAMERA_TILT_MAX_ANGLE = CAMERA_CONFIG['tilt_range']
```

### Beneficis
- Més fàcil modificar la configuració
- Constants relacionades agrupades
- Menys repetició (pan i tilt tenen els mateixos valors)

---

## TASCA 2: Eliminar duplicació en càlculs de pan/tilt

**Prioritat**: Alta  
**Esforç**: Baix  
**Impacte**: Mantenibilitat, DRY

### Descripció
Els càlculs de pan i tilt a `processar_iteracio_tracking` són gairebé idèntics. Extreure a una funció helper.

### Codi actual (línies 216-239)
```python
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
```

### Proposta
```python
def calcular_i_actualitzar_angle(posicio, dimensio_camera, angle_actual, 
                                   angle_min, angle_max, invertir=False):
    """Calcula i actualitza un angle de càmera."""
    canvi_desitjat = calcular_canvi_angle(posicio, dimensio_camera, invertir)
    return actualitzar_angle_camera(angle_actual, canvi_desitjat, angle_min, angle_max)

# Ús:
nou_pan_angle = calcular_i_actualitzar_angle(
    posicio_suavitzada_x, CAMERA_WIDTH, pan_angle,
    CAMERA_PAN_MIN_ANGLE, CAMERA_PAN_MAX_ANGLE, invertir=False
)
nou_tilt_angle = calcular_i_actualitzar_angle(
    posicio_suavitzada_y, CAMERA_HEIGHT, tilt_angle,
    CAMERA_TILT_MIN_ANGLE, CAMERA_TILT_MAX_ANGLE, invertir=True
)
```

### Beneficis
- Elimina duplicació de codi (DRY)
- Més fàcil mantenir
- Codi més compacte

---

## TASCA 3: Crear classe/dataclass per gestionar l'estat del seguiment

**Prioritat**: Mitjana  
**Esforç**: Mitjà  
**Impacte**: Organització, tipat

### Descripció
En lloc d'utilitzar un diccionari simple per l'estat, crear una classe o dataclass.

### Codi actual
```python
state = {'centered': False}
state_lock = threading.Lock()
```

### Proposta
```python
from dataclasses import dataclass
from threading import Lock

@dataclass
class TrackingState:
    centered: bool = False
    
    def __post_init__(self):
        self.lock = Lock()
```

O amb classe completa:
```python
class TrackingState:
    def __init__(self):
        self.centered = False
        self.lock = Lock()
    
    def is_centered(self):
        with self.lock:
            return self.centered
    
    def set_centered(self, value):
        with self.lock:
            self.centered = value
```

### Beneficis
- Més fàcil afegir nous camps d'estat (futur: FASE 4)
- Millor encapsulació
- Pot afegir tipat estàtic
- Mètodes helpers per gestionar l'estat

---

## TASCA 4: Consolidar validacions de paràmetres

**Prioritat**: Baixa  
**Esforç**: Baix  
**Impacte**: Llegibilitat

### Descripció
Les validacions a `create_visual_tracking_handler` es poden consolidar.

### Codi actual (línies 301-316)
```python
if car is None:
    raise ValueError("car no pot ser None")

if not isinstance(with_img, bool):
    raise ValueError("with_img ha de ser un boolean")

if not isinstance(default_head_tilt, (int, float)):
    raise ValueError("default_head_tilt ha de ser un número")

default_head_tilt = clamp_number(
    default_head_tilt,
    CAMERA_TILT_MIN_ANGLE,
    CAMERA_TILT_MAX_ANGLE
)
```

### Proposta
```python
def _validar_parametres(car, with_img, default_head_tilt):
    """Valida els paràmetres d'entrada."""
    if car is None:
        raise ValueError("car no pot ser None")
    
    if not isinstance(with_img, bool):
        raise ValueError("with_img ha de ser un boolean")
    
    if not isinstance(default_head_tilt, (int, float)):
        raise ValueError("default_head_tilt ha de ser un número")
    
    return clamp_number(
        default_head_tilt,
        CAMERA_TILT_MIN_ANGLE,
        CAMERA_TILT_MAX_ANGLE
    )

# Ús:
default_head_tilt = _validar_parametres(car, with_img, default_head_tilt)
```

### Beneficis
- Separació de responsabilitats
- Codi més net
- Més fàcil de testar les validacions per separat

---

## TASCA 5: Millorar gestió de detection_history

**Prioritat**: Baixa  
**Esforç**: Baix  
**Impacte**: Organització

### Descripció
En lloc d'un diccionari simple, utilitzar una classe helper per gestionar l'històric.

### Codi actual
```python
detection_history = {'x': [], 'y': []}
# ...
if len(detection_history['x']) > DETECTION_HISTORY_SIZE:
    detection_history['x'].pop(0)
    detection_history['y'].pop(0)
```

### Proposta
```python
class DetectionHistory:
    def __init__(self, max_size=DETECTION_HISTORY_SIZE):
        self.x = []
        self.y = []
        self.max_size = max_size
    
    def add(self, x, y):
        self.x.append(x)
        self.y.append(y)
        if len(self.x) > self.max_size:
            self.x.pop(0)
            self.y.pop(0)
    
    def clear(self):
        self.x.clear()
        self.y.clear()
```

### Beneficis
- Encapsulació de la lògica
- Més fàcil mantenir la coherència entre x i y
- Pot afegir mètodes helpers (ex: obtenir última posició)

---

## TASCA 6: Simplificar calcular_mitjana_ponderada

**Prioritat**: Baixa  
**Esforç**: Baix  
**Impacte**: Llegibilitat

### Descripció
El cas especial per un sol valor es pot simplificar.

### Codi actual (línies 60-64)
```python
if not valors:
    return 0.0

if len(valors) == 1:
    return float(valors[0])
```

### Proposta
```python
if not valors:
    return 0.0

# El cas de 1 valor es gestiona automàticament per la resta del codi
# No cal cas especial
```

O mantenir però amb comentari explicatiu:
```python
if not valors:
    return 0.0

# Cas especial: amb un sol valor, retornar-lo directament
# (evita càlculs innecessaris)
if len(valors) == 1:
    return float(valors[0])
```

### Beneficis
- Codi més simple o millor documentat
- Menys casos especials

---

## TASCA 7: Extreure constants màgiques a constants nombrats

**Prioritat**: Baixa  
**Esforç**: Baix  
**Impacte**: Llegibilitat

### Descripció
Hi ha algunes constants màgiques que es podrien nombrar.

### Codi actual
```python
canvi = (coordenada * 10 / dimensio_camera) - 5  # línia 99
```

### Proposta
```python
# Constants per al càlcul d'angles
ANGLE_SCALE_FACTOR = 10
ANGLE_OFFSET = 5

canvi = (coordenada * ANGLE_SCALE_FACTOR / dimensio_camera) - ANGLE_OFFSET
```

### Beneficis
- Més fàcil entendre el càlcul
- Més fàcil ajustar si cal

---

## RESUM DE PRIORITATS

### Alta Prioritat
1. **TASCA 2**: Eliminar duplicació en càlculs de pan/tilt (DRY)

### Mitjana Prioritat
2. **TASCA 1**: Extreure constants de càmera a configuració agrupada
3. **TASCA 3**: Crear classe/dataclass per gestionar l'estat

### Baixa Prioritat
4. **TASCA 4**: Consolidar validacions de paràmetres
5. **TASCA 5**: Millorar gestió de detection_history
6. **TASCA 6**: Simplificar calcular_mitjana_ponderada
7. **TASCA 7**: Extreure constants màgiques

---

## NOTES

- Les tasques estan ordenades per prioritat i esforç
- Es recomana començar per la TASCA 2 (alta prioritat, baix esforç)
- Les tasques de baixa prioritat són millores menors que es poden fer gradualment
- Totes les tasques mantenen la compatibilitat amb el codi existent i els tests


