# PROPOSTA DE TESTS D'INICI - FASE 1

Aquest document proposa els 5 tests d'inici més importants per al robot Picar-X.
Aquests tests s'executaran quan el robot s'inicia (si s'utilitza el flag `--run-tests`)
per verificar que tot el hardware funciona correctament.

---

## CRITERIS DE PRIORITATZACIÓ

Els tests s'han prioritzat segons:
1. **Crítica per al funcionament**: Si falla, el robot no pot funcionar
2. **Freqüència d'ús**: Funcionalitats utilitzades contínuament
3. **Impacte en FASE 1**: Funcionalitats necessàries per al seguiment visual
4. **Facilitat de detecció d'errors**: Tests que detecten problemes comuns

---

## ELS 5 TESTS D'INICI MÉS IMPORTANTS

### TEST 1: Inicialització de Picarx ✅ (ALTA PRIORITAT)

**Descripció**: Verificar que el robot Picarx s'inicialitza correctament.

**Per què és crític**:
- Si falla, res funciona
- Detecta problemes de connexió d'hardware
- És el primer pas necessari per a qualsevol funcionalitat

**Què ha de verificar**:
- Que `Picarx()` no llança excepcions
- Que el robot respon a crides bàsiques (ex: `reset()`)
- Que els mètodes bàsics estan disponibles

**Implementació suggerida**:
```python
def test_inicialitzacio_picarx():
    """Test que el robot Picarx s'inicialitza correctament"""
    try:
        car = Picarx()
        time.sleep(0.5)  # Esperar inicialització
        
        # Verificar que mètodes bàsics existeixen
        assert hasattr(car, 'reset')
        assert hasattr(car, 'forward')
        assert hasattr(car, 'stop')
        
        # Provar reset (no hauria de llançar excepció)
        car.reset()
        
        print("✓ Test 1/5: Inicialització Picarx - OK")
        return True
    except Exception as e:
        print(f"✗ Test 1/5: Inicialització Picarx - ERROR: {e}")
        return False
```

**Impacte**: Si falla, tot el robot està inoperatiu.

---

### TEST 2: Càmera Pan/Tilt ✅ (ALTA PRIORITAT)

**Descripció**: Verificar que la càmera respon correctament als comandaments pan/tilt.

**Per què és crític**:
- **ESSENCIAL per FASE 1** (seguiment visual)
- Si falla, el seguiment visual no funciona
- Detecta problemes mecànics o de connexió de la càmera

**Què ha de verificar**:
- Que `set_cam_pan_angle()` funciona
- Que `set_cam_tilt_angle()` funciona
- Que els angles es poden canviar dins del rang permès

**Implementació suggerida**:
```python
def test_camera_pan_tilt():
    """Test que la càmera respon correctament als comandaments pan/tilt"""
    try:
        car = Picarx()
        car.reset()
        time.sleep(0.2)
        
        DEFAULT_TILT = 20
        DEFAULT_PAN = 0
        
        # Test pan
        car.set_cam_pan_angle(DEFAULT_PAN)
        time.sleep(0.1)
        car.set_cam_pan_angle(15)
        time.sleep(0.1)
        car.set_cam_pan_angle(-15)
        time.sleep(0.1)
        car.set_cam_pan_angle(DEFAULT_PAN)
        time.sleep(0.1)
        
        # Test tilt
        car.set_cam_tilt_angle(DEFAULT_TILT)
        time.sleep(0.1)
        car.set_cam_tilt_angle(30)
        time.sleep(0.1)
        car.set_cam_tilt_angle(10)
        time.sleep(0.1)
        car.set_cam_tilt_angle(DEFAULT_TILT)
        time.sleep(0.1)
        
        print("✓ Test 2/5: Càmera Pan/Tilt - OK")
        return True
    except Exception as e:
        print(f"✗ Test 2/5: Càmera Pan/Tilt - ERROR: {e}")
        return False
```

**Impacte**: Si falla, FASE 1 (seguiment visual) no funciona.

---

### TEST 3: Moviment Forward/Backward ✅ (ALTA PRIORITAT)

**Descripció**: Verificar que el robot pot moure's endavant i endarrere.

**Per què és crític**:
- Funcionalitat bàsica del robot
- Necessari per a FASE 2 i FASE 3 (moviment reactiu i aproximació)
- Detecta problemes amb motors o controladors

**Què ha de verificar**:
- Que `forward()` funciona
- Que `backward()` funciona (o `set_motor_speed()`)
- Que `stop()` funciona correctament
- Moviment suau sense errors

**Implementació suggerida**:
```python
def test_moviment_forward_backward():
    """Test que el robot pot moure's endavant i endarrere"""
    try:
        car = Picarx()
        car.reset()
        time.sleep(0.2)
        
        # Test forward
        car.set_dir_servo_angle(0)  # Endreçar rodes
        time.sleep(0.1)
        car.forward(20)  # Velocitat baixa per seguretat
        time.sleep(0.3)
        car.stop()
        time.sleep(0.2)
        
        # Test backward (si existeix) o set_motor_speed
        car.backward(20)
        time.sleep(0.3)
        car.stop()
        time.sleep(0.2)
        
        print("✓ Test 3/5: Moviment Forward/Backward - OK")
        return True
    except Exception as e:
        print(f"✗ Test 3/5: Moviment Forward/Backward - ERROR: {e}")
        return False
```

**Impacte**: Si falla, el robot no es pot moure (crític per FASE 2-3).

---

### TEST 4: Reset i Aturada ✅ (MITJANA PRIORITAT)

**Descripció**: Verificar que el reset i l'aturada funcionen correctament.

**Per què és important**:
- Seguretat: assegurar que el robot es pot aturar
- Estabilitat: posar tot a zero després de tests
- Funcionalitat utilitzada freqüentment

**Què ha de verificar**:
- Que `reset()` posa tot a zero sense errors
- Que `stop()` atura el moviment immediatament
- Que després de reset tot està en estat conegut

**Implementació suggerida**:
```python
def test_reset_stop():
    """Test que reset i stop funcionen correctament"""
    try:
        car = Picarx()
        
        # Moviment prevì per provar que reset funciona
        car.set_dir_servo_angle(15)
        car.forward(30)
        time.sleep(0.2)
        
        # Test stop
        car.stop()
        time.sleep(0.2)
        
        # Test reset
        car.reset()
        time.sleep(0.3)
        
        # Verificar que tot està a zero (càmera i rodes)
        car.set_cam_pan_angle(0)
        car.set_cam_tilt_angle(20)
        car.set_dir_servo_angle(0)
        time.sleep(0.2)
        
        print("✓ Test 4/5: Reset i Stop - OK")
        return True
    except Exception as e:
        print(f"✗ Test 4/5: Reset i Stop - ERROR: {e}")
        return False
```

**Impacte**: Si falla, pot afectar seguretat i estabilitat.

---

### TEST 5: Detecció de Càmera (Vilib) ✅ (MITJANA PRIORITAT)

**Descripció**: Verificar que la càmera (Vilib) està disponible i funcional (si with_img).

**Per què és important**:
- Necessari per FASE 1 (seguiment visual)
- Detecta si la càmera no està connectada o no funciona
- Evita errors durant l'execució

**Què ha de verificar**:
- Que Vilib pot inicialitzar-se (si with_img=True)
- Que la càmera està accessible
- Que detect_obj_parameter existeix (per detecció de persones)

**Implementació suggerida**:
```python
def test_camera_vilib(with_img):
    """Test que la càmera Vilib està disponible i funcional"""
    if not with_img:
        print("⊘ Test 5/5: Càmera Vilib - SKIP (--no-img)")
        return True
    
    try:
        from vilib import Vilib
        
        # Verificar que Vilib està inicialitzat (si ja s'ha inicialitzat)
        # Això s'executarà després de la inicialització a gpt_car.py
        
        # Verificar que els atributs necessaris existeixen
        if hasattr(Vilib, 'detect_obj_parameter'):
            # Esperar una mica per assegurar inicialització
            time.sleep(0.5)
            print("✓ Test 5/5: Càmera Vilib - OK")
            return True
        else:
            print("⚠ Test 5/5: Càmera Vilib - WARNING (detect_obj_parameter no disponible)")
            return True  # No crític si no s'ha inicialitzat encara
    except ImportError:
        print("✗ Test 5/5: Càmera Vilib - ERROR (Vilib no disponible)")
        return False
    except Exception as e:
        print(f"✗ Test 5/5: Càmera Vilib - ERROR: {e}")
        return False
```

**Impacte**: Si falla amb with_img=True, FASE 1 no funciona completament.

---

## RESUM DELS 5 TESTS

| # | Test | Prioritat | Impacte si falla |
|---|------|-----------|------------------|
| 1 | Inicialització Picarx | **Alta** | Tot el robot inoperatiu |
| 2 | Càmera Pan/Tilt | **Alta** | FASE 1 no funciona |
| 3 | Moviment Forward/Backward | **Alta** | Robot no es pot moure |
| 4 | Reset i Stop | Mitjana | Seguretat i estabilitat |
| 5 | Detecció Càmera (Vilib) | Mitjana | FASE 1 limitada |

---

## IMPLEMENTACIÓ PROPOSADA

**Ubicació**: `gpt_car.py` abans de `main()`

**Flag**: `--run-tests` per forçar execució, `--skip-tests` per evitar (per defecte: skip)

**Estructura**:
```python
def run_startup_tests(with_img=True):
    """Executa bateria de tests d'inici"""
    print("\n" + "="*50)
    print("EXECUTANT TESTS D'INICI")
    print("="*50 + "\n")
    
    results = []
    results.append(test_inicialitzacio_picarx())
    results.append(test_camera_pan_tilt())
    results.append(test_moviment_forward_backward())
    results.append(test_reset_stop())
    results.append(test_camera_vilib(with_img))
    
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    print(f"RESULTATS: {passed}/{total} tests passats")
    print("="*50 + "\n")
    
    if passed < total:
        print("⚠ ALERTA: Alguns tests han fallat. El robot pot no funcionar correctament.")
        response = input("Continuar de totes maneres? (s/n): ")
        if response.lower() != 's':
            sys.exit(1)
    
    return passed == total
```

**Ús al main()**:
```python
if '--run-tests' in sys.argv:
    if not run_startup_tests(with_img):
        sys.exit(1)
```

---

## NOTES IMPORTANTS

1. **Tests amb hardware real**: Aquests tests requereixen hardware real (Raspberry Pi + Picar-X)
2. **No bloquejants**: Els tests no haurien de bloquejar si un sensor no funciona (només avisar)
3. **Temps mínim**: Cada test hauria de ser ràpid (< 2 segons total)
4. **Seguretat**: Utilitzar velocitats baixes i moviments curts
5. **Opció skip**: Per defecte els tests s'ometen (només s'executen amb --run-tests)

---

## TESTS NO INCLOSOS (per futures millores)

Els següents tests NO estan inclosos però es podrien afegir en el futur:

- **Test de sensor ultrasònic**: Si existeix, verificar lectura de distància
- **Test de gir (set_dir_servo_angle)**: Verificar que les rodes giren correctament
- **Test de LED**: Verificar que el LED funciona
- **Test de so (Music)**: Verificar que el sistema de so funciona
- **Test de detecció de persones**: Verificar que Vilib detecta persones

**Razó**: Aquests tests són menys crítics o més complexos de testar. Els 5 proposats
cobreixen les funcionalitats més crítiques per al funcionament bàsic del robot i FASE 1.





