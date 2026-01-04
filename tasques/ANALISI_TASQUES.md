# ANÀLISI DE TASQUES - PLA DE MILLORA PICAR-X

Data d'anàlisi: Generat automàticament

Aquest document analitza l'estat d'implementació de les tasques definides al pla de millora per al seguiment de persones del picar-x.

---

## RESUM EXECUTIU

- **FASE 1**: ✅ **COMPLETADA** (amb algunes tasques de finalització pendents)
- **FASE 2**: ❌ **NO INICIADA**
- **FASE 3**: ❌ **NO INICIADA**
- **FASE 4**: ❌ **NO INICIADA**
- **FASE 5**: ❌ **NO INICIADA** (Opcional)

---

## FASE 1: SEGUIMENT VISUAL PUR (Base)

### Estat: ✅ COMPLETADA (implementació)

#### 1.1. Implementar seguiment de càmera (pan/tilt) basat en stare_at_you.py
**Estat**: ✅ **COMPLETAT**

**Evidències**:
- Fitxer `visual_tracking.py` implementat completament
- Funció `create_visual_tracking_handler()` crea handler per seguiment visual
- Funció `processar_iteracio_tracking()` processa deteccions i mou càmera
- Funció `aplicar_angles_camera()` aplica angles pan/tilt a la càmera
- Integrat a `gpt_car.py` (línies 308-338)
- Thread de seguiment visual iniciat a `gpt_car.py` línia 338

**Codi rellevant**:
- `visual_tracking.py`: Implementació completa
- `gpt_car.py` línies 308-338: Integració del seguiment visual

---

#### 1.2. Afegir filtre de suavització per càmera
**Estat**: ✅ **COMPLETAT**

**Evidències**:
- Implementat mitjana ponderada de 5 deteccions (`DETECTION_HISTORY_SIZE = 5`)
- Funció `calcular_mitjana_ponderada()` implementada (línies 49-73)
- Pesos definits: `SMOOTHING_WEIGHTS = [0.1, 0.15, 0.2, 0.25, 0.3]`
- Limitació de velocitat: `MAX_ANGLE_CHANGE_PER_ITERATION = 3` graus per iteració
- Funció `actualitzar_angle_camera()` aplica limitació de velocitat (línies 255-277)

**Codi rellevant**:
- `visual_tracking.py` línies 18-19, 26: Constants de configuració
- `visual_tracking.py` línies 49-73: Funció de mitjana ponderada
- `visual_tracking.py` línies 255-277: Limitació de velocitat

---

#### 1.3. Detectar quan la persona està "centrada"
**Estat**: ✅ **COMPLETAT**

**Evidències**:
- Zona central definida: `CENTER_ZONE_TOLERANCE = 30` píxels (línia 16)
- Detecció implementada a `processar_deteccio_persona()` (línies 155-159)
- Estat compartit thread-safe: `state['centered']` (línia 319)
- Funció `is_person_centered()` exposada per consultar estat (línies 361-370)
- Integrat al handler principal

**Codi rellevant**:
- `visual_tracking.py` línia 16: Constant de tolerància
- `visual_tracking.py` línies 155-163: Lògica de detecció de centrat
- `visual_tracking.py` línies 361-370: Funció de consulta

---

### Tasques de Finalització de FASE 1

#### 1. Refactorització
**Estat**: ⚠️ **PARCIALMENT COMPLETAT**

**Completat**:
- ✅ Comentaris escrits en català
- ✅ Codi modularitzat (separat en funcions lògiques)
- ✅ Noms de variables i funcions clars
- ✅ Gestió adequada d'errors

**Pendent**:
- ⚠️ Cal revisar si hi ha codi duplicat (DRY)
- ⚠️ Cal revisar classes/mètodes innecessaris
- ⚠️ Cal revisar imports optimitzats
- ⚠️ Cal revisar principis SOLID aplicats

**Cobertura actual**: 11.11% (objectiu: 70% mínim per a codi nou)
- `visual_tracking.py`: 21.55% de cobertura
- Cal millorar cobertura especialment de funcions principals del handler

---

#### 2. Validació de qualitat del codi i seguretat
**Estat**: ✅ **BONAMENT COMPLETAT**

**Completat**:
- ✅ Gestió d'errors i excepcions (try/except als handlers)
- ✅ Validació d'inputs i paràmetres (validació a `create_visual_tracking_handler()`)
- ✅ Gestió de recursos (locks per thread-safety)
- ✅ Gestió correcta de threads (daemon threads)
- ✅ Validació de coordenades (clamp_number per limitar valors)

**Evidències**:
- `visual_tracking.py` línies 302-316: Validació de paràmetres
- `visual_tracking.py` línies 129-130: Validació de coordenades
- `visual_tracking.py` línia 320: Lock per thread-safety
- `visual_tracking.py` línies 357-359: Gestió d'excepcions

---

#### 3. Creació/actualització de test unitaris
**Estat**: ✅ **COMPLETAT**

**Evidències**:
- Fitxer `tests/test_visual_tracking.py` creat amb 135 tests en total
- Tests per a totes les funcions principals:
  - `test_clamp_number`: 4 tests
  - `test_calcular_mitjana_ponderada`: 5 tests
  - `test_calcular_canvi_angle`: 6 tests
  - `test_actualitzar_angle_camera`: 5 tests
  - `test_create_visual_tracking_handler`: 6 tests
  - `test_processar_deteccio_persona`: 5 tests
  - `test_aplicar_angles_camera`: 3 tests
  - `test_processar_iteracio_tracking`: 3 tests
  - Altres tests de handlers: 8+ tests

**Cobertura**:
- Total projecte: 11.11%
- `visual_tracking.py`: 21.55%
- ⚠️ **NO assoleix el 70% mínim requerit** per a codi nou

**Pendent**:
- ⚠️ Millorar cobertura fins al 70% mínim
- Tests utilitzen mocks adequadament
- Tests són independents i repetibles

---

#### 4. Creació/actualització de bateria de tests d'inici
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- ❌ No hi ha tests d'inici quan el robot s'inicia
- ❌ No hi ha tests de sensors (ultrasònic, càmera)
- ❌ No hi ha tests de moviment bàsic (endavant, endarrere, gir)
- ❌ No hi ha tests de càmera (pan/tilt)
- ❌ No hi ha flag `--skip-tests` o `--run-tests` a `gpt_car.py`

**Requeriments**:
- Implementar tests d'inici al `main()` de `gpt_car.py`
- Afegir opció `--skip-tests` per evitar tests en execucions normals
- Afegir opció `--run-tests` per forçar tests d'inici

---

#### 5. Detecció de deute tècnic
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- ❌ No existeix fitxer `deute_tecnic.txt`
- ❌ No hi ha documentació de decisions tècniques preses per rapidesa
- ❌ No hi ha documentació de codi que necessita millores futures
- ❌ No hi ha documentació de limitacions conegudes
- ❌ No hi ha documentació de dependències problemàtiques

**Recomanació**:
Crear fitxer `deute_tecnic.txt` amb:
- Decisions tècniques preses per rapidesa a FASE 1
- Codi que necessita millores futures
- Limitacions conegudes del seguiment visual
- Dependències problemàtiques (si n'hi ha)

---

#### 6. Actualització del README
**Estat**: ⚠️ **PARCIALMENT COMPLETAT**

**Completat**:
- ✅ README.md existeix i està actualitzat
- ✅ Estructura del projecte documentada
- ✅ `visual_tracking.py` mencionat a l'estructura

**Pendent**:
- ⚠️ No menciona específicament que FASE 1 està completada
- ⚠️ No documenta les noves funcionalitats de seguiment visual
- ⚠️ No explica com utilitzar el seguiment visual
- ⚠️ No documenta les funcionalitats implementades de FASE 1

**Recomanació**:
Afegir secció al README documentant:
- Funcionalitat de seguiment visual (FASE 1 completada)
- Com funciona el seguiment visual
- Configuració i ús

---

## FASE 2: MOVIMENT REACTIU (Quan surt del camp de visió)

### Estat: ❌ NO INICIADA

#### 2.1. Detectar quan la persona surt del camp de visió
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- Detectar quan no es detecta persona durant 0.5s
- Recordar última posició coneguda (dreta/esquerra)
- Girar el robot cap a la direcció on va la persona

**Nota**: El seguiment visual actual detecta quan no hi ha persona (buida detection_history), però no hi ha lògica per moure el robot.

---

#### 2.2. Estratègia de recerca
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- Girar 30 graus cap a la direcció on va la persona
- Aturar i buscar amb càmera
- Si no es troba, girar una mica més
- Repetir fins a trobar o timeout (5s)

---

#### 2.3. Quan es troba de nou
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- Centrar amb càmera primer (això ja funciona amb FASE 1)
- Després moure cap a la persona si està massa lluny (això seria FASE 3)

---

## FASE 3: APROXIMACIÓ QUAN ESTÀ CENTRADA

### Estat: ❌ NO INICIADA

#### 3.1. Quan la persona està centrada a la imatge
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- Llegir distància amb sensor ultrasònic
- Si distància > OPTIMAL_DISTANCE + 10cm: avançar lentament
- Si distància < OPTIMAL_DISTANCE - 10cm: retrocedir lentament
- Si està dins zona òptima: aturar

**Nota**: La detecció de persona centrada ja existeix (FASE 1), però no hi ha lògica per moure el robot basant-se en distància.

---

#### 3.2. Velocitat adaptativa
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- Velocitat proporcional a l'error de distància
- Màxim 30% de velocitat
- Aturar si error < 5cm

---

## FASE 4: ESTATS I MÀQUINA D'ESTATS

### Estat: ❌ NO INICIADA

#### 4.1. Definir estats del sistema
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- `STATE_SEARCHING`: Buscant persona (girant, movent càmera)
- `STATE_TRACKING`: Seguint amb càmera (persona visible)
- `STATE_APPROACHING`: Aproximant-se (persona centrada, ajustant distància)
- `STATE_LOST`: Persona perduda (recerca activa)

**Nota**: Actualment només hi ha un estat simple `state['centered']` (boolean) a FASE 1.

---

#### 4.2. Transicions d'estat
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- Implementar tots els transicions entre estats definides al pla

---

#### 4.3. Comportament per estat
**Estat**: ❌ **NO IMPLEMENTAT**

**Pendent**:
- Implementar comportament clar per cada estat

---

## FASE 5: MILLORES AVANÇADES (Opcional)

### Estat: ❌ NO INICIADA

#### 5.1. Predicció de moviment
**Estat**: ❌ **NO IMPLEMENTAT** (Opcional)

#### 5.2. Evitació d'obstacles
**Estat**: ❌ **NO IMPLEMENTAT** (Opcional)

#### 5.3. Seguiment de múltiples persones
**Estat**: ❌ **NO IMPLEMENTAT** (Opcional)

---

## RESUM PER CATEGORIA

### Implementació de Funcionalitats

| Fase | Estat | Progress |
|------|-------|----------|
| FASE 1 | ✅ Completada | 100% |
| FASE 2 | ❌ No iniciada | 0% |
| FASE 3 | ❌ No iniciada | 0% |
| FASE 4 | ❌ No iniciada | 0% |
| FASE 5 | ❌ No iniciada | 0% (Opcional) |

### Tasques de Finalització (FASE 1)

| Tasca | Estat | Notes |
|-------|-------|-------|
| Refactorització | ⚠️ Parcial | Codi net però pot millorar |
| Validació qualitat | ✅ Completat | Bona gestió d'errors |
| Tests unitaris | ✅ Completat | ⚠️ Cobertura baixa (21.55% vs 70% objectiu) |
| Tests d'inici | ❌ No implementat | Cal implementar |
| Deute tècnic | ❌ No implementat | Cal crear fitxer |
| README | ⚠️ Parcial | Actualitzat però falta detall FASE 1 |

---

## PRIORITATS RECOMANADES

### Alta Prioritat (Completar FASE 1)

1. **Millorar cobertura de tests fins al 70%** (actualment 21.55%)
   - Afegir més tests per a funcions principals
   - Tests d'integració per al handler complet

2. **Crear fitxer deute_tecnic.txt**
   - Documentar decisions de FASE 1
   - Documentar limitacions conegudes

3. **Implementar tests d'inici**
   - Afegir flag `--skip-tests` / `--run-tests`
   - Tests de sensors i moviment bàsic

4. **Actualitzar README amb detalls de FASE 1**
   - Documentar funcionalitats implementades
   - Explicar com utilitzar el seguiment visual

### Mitjana Prioritat (Iniciar FASE 2)

5. **Implementar FASE 2: Moviment reactiu**
   - Detectar quan persona surt del camp de visió
   - Estratègia de recerca
   - Girar robot cap a persona perduda

### Baixa Prioritat (Futur)

6. **FASE 3**: Aproximació quan està centrada
7. **FASE 4**: Màquina d'estats
8. **FASE 5**: Millores avançades (opcional)

---

## NOTES FINALS

- La **FASE 1 està completada funcionalment** però li falten algunes tasques de finalització
- El codi està ben estructurat i documentat
- Els tests existeixen però la cobertura és baixa
- Cal completar les tasques de finalització abans de considerar FASE 1 100% completa
- Les fases següents (2-5) no han estat iniciades

**Recomanació**: Completar les tasques de finalització de FASE 1 abans de continuar amb FASE 2.

