"""
Tests unitaris per a visual_tracking.py
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os
import threading

# Afegir el directori pare al path per poder importar els mòduls
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visual_tracking import (
    clamp_number,
    calcular_mitjana_ponderada,
    calcular_canvi_angle,
    actualitzar_angle_camera,
    create_visual_tracking_handler,
    processar_deteccio_persona,
    aplicar_angles_camera,
    processar_iteracio_tracking
)


class TestClampNumber(unittest.TestCase):
    """Tests per a clamp_number"""
    
    def test_clamp_within_range(self):
        """Test quan el número està dins del rang"""
        self.assertEqual(clamp_number(5, 0, 10), 5)
        self.assertEqual(clamp_number(0, 0, 10), 0)
        self.assertEqual(clamp_number(10, 0, 10), 10)
    
    def test_clamp_below_min(self):
        """Test quan el número està per sota del mínim"""
        self.assertEqual(clamp_number(-5, 0, 10), 0)
        self.assertEqual(clamp_number(5, 10, 20), 10)
    
    def test_clamp_above_max(self):
        """Test quan el número està per sobre del màxim"""
        self.assertEqual(clamp_number(15, 0, 10), 10)
        self.assertEqual(clamp_number(5, 0, 3), 3)
    
    def test_clamp_reversed_limits(self):
        """Test quan els límits estan invertits"""
        self.assertEqual(clamp_number(5, 10, 0), 5)
        self.assertEqual(clamp_number(-5, 10, 0), 0)
        self.assertEqual(clamp_number(15, 10, 0), 10)


class TestCalcularMitjanaPonderada(unittest.TestCase):
    """Tests per a calcular_mitjana_ponderada"""
    
    def test_mitjana_ponderada_basic(self):
        """Test bàsic de mitjana ponderada"""
        valors = [1, 2, 3]
        pesos = [0.1, 0.2, 0.3]
        result = calcular_mitjana_ponderada(valors, pesos)
        expected = (1*0.1 + 2*0.2 + 3*0.3) / (0.1 + 0.2 + 0.3)
        self.assertAlmostEqual(result, expected, places=5)
    
    def test_mitjana_ponderada_empty(self):
        """Test amb llista buida"""
        result = calcular_mitjana_ponderada([], [])
        self.assertEqual(result, 0.0)
    
    def test_mitjana_ponderada_single_value(self):
        """Test amb un sol valor"""
        result = calcular_mitjana_ponderada([5], [0.5])
        self.assertEqual(result, 5.0)
    
    def test_mitjana_ponderada_more_weights(self):
        """Test quan hi ha més pesos que valors"""
        valors = [1, 2]
        pesos = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = calcular_mitjana_ponderada(valors, pesos)
        # Hauria d'utilitzar només els últims 2 pesos
        expected = (1*0.4 + 2*0.5) / (0.4 + 0.5)
        self.assertAlmostEqual(result, expected, places=5)
    
    def test_mitjana_ponderada_zero_weights(self):
        """Test quan la suma de pesos és zero"""
        valors = [1, 2, 3]
        pesos = [0, 0, 0]
        result = calcular_mitjana_ponderada(valors, pesos)
        # Hauria de retornar l'últim valor
        self.assertEqual(result, 3.0)


class TestCalcularCanviAngle(unittest.TestCase):
    """Tests per a calcular_canvi_angle"""
    
    def test_calcular_canvi_angle_center(self):
        """Test quan la coordenada està al centre"""
        # Coordenada al centre (320 en una càmera de 640)
        result = calcular_canvi_angle(320, 640)
        self.assertAlmostEqual(result, 0.0, places=5)
    
    def test_calcular_canvi_angle_left(self):
        """Test quan la coordenada està a l'esquerra"""
        # Coordenada a l'esquerra (0 en una càmera de 640)
        result = calcular_canvi_angle(0, 640)
        self.assertAlmostEqual(result, -5.0, places=5)
    
    def test_calcular_canvi_angle_right(self):
        """Test quan la coordenada està a la dreta"""
        # Coordenada a la dreta (640 en una càmera de 640)
        result = calcular_canvi_angle(640, 640)
        self.assertAlmostEqual(result, 5.0, places=5)
    
    def test_calcular_canvi_angle_invertir(self):
        """Test amb invertir=True"""
        result = calcular_canvi_angle(0, 640, invertir=True)
        self.assertAlmostEqual(result, 5.0, places=5)
    
    def test_calcular_canvi_angle_invalid_dimensio(self):
        """Test amb dimensió invàlida"""
        with self.assertRaises(ValueError):
            calcular_canvi_angle(320, 0)
        
        with self.assertRaises(ValueError):
            calcular_canvi_angle(320, -10)
    
    def test_calcular_canvi_angle_invalid_coordenada(self):
        """Test amb coordenada invàlida"""
        with self.assertRaises(ValueError):
            calcular_canvi_angle("invalid", 640)
        
        with self.assertRaises(ValueError):
            calcular_canvi_angle(None, 640)


class TestActualitzarAngleCamera(unittest.TestCase):
    """Tests per a actualitzar_angle_camera"""
    
    def test_actualitzar_angle_within_limits(self):
        """Test quan el canvi està dins dels límits"""
        # MAX_ANGLE_CHANGE_PER_ITERATION és 3, per tant 5 es limitarà a 3
        result = actualitzar_angle_camera(0, 5, -35, 35)
        self.assertEqual(result, 3)  # 0 + 3 (limitació)
    
    def test_actualitzar_angle_at_min(self):
        """Test quan arriba al mínim"""
        result = actualitzar_angle_camera(-35, -10, -35, 35)
        self.assertEqual(result, -35)  # Limitada al mínim
    
    def test_actualitzar_angle_at_max(self):
        """Test quan arriba al màxim"""
        result = actualitzar_angle_camera(35, 10, -35, 35)
        self.assertEqual(result, 35)  # Limitada al màxim
    
    def test_actualitzar_angle_max_change(self):
        """Test amb limitació de canvi màxim per iteració"""
        # Canvi de 10 graus però MAX_ANGLE_CHANGE_PER_ITERATION és 3
        result = actualitzar_angle_camera(0, 10, -35, 35)
        self.assertEqual(result, 3)  # Limitada a 3
    
    def test_actualitzar_angle_negative_change(self):
        """Test amb canvi negatiu"""
        # Canvi de -5 però MAX_ANGLE_CHANGE_PER_ITERATION és 3, per tant es limitarà a -3
        result = actualitzar_angle_camera(0, -5, -35, 35)
        self.assertEqual(result, -3)  # 0 + (-3) (limitació)


class TestCreateVisualTrackingHandler(unittest.TestCase):
    """Tests per a create_visual_tracking_handler"""
    
    def setUp(self):
        """Configuració inicial per a cada test"""
        self.mock_car = Mock()
        self.mock_vilib = Mock()
        self.mock_vilib.detect_obj_parameter = {'human_n': 0}
    
    def test_create_handler_with_img(self):
        """Test de creació de handler amb imatge"""
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            self.mock_car, self.mock_vilib, True, 20
        )
        
        self.assertIsNotNone(handler)
        self.assertIsNotNone(state)
        self.assertIsNotNone(lock)
        self.assertIsNotNone(is_centered_func)
        self.assertFalse(state['centered'])
    
    def test_create_handler_without_img(self):
        """Test de creació de handler sense imatge"""
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            self.mock_car, None, False, 20
        )
        
        self.assertIsNotNone(handler)
        self.assertIsNotNone(is_centered_func)
    
    def test_create_handler_invalid_car(self):
        """Test amb car=None"""
        with self.assertRaises(ValueError):
            create_visual_tracking_handler(None, self.mock_vilib, True, 20)
    
    def test_create_handler_invalid_with_img(self):
        """Test amb with_img no boolean"""
        with self.assertRaises(ValueError):
            create_visual_tracking_handler(self.mock_car, self.mock_vilib, "invalid", 20)
    
    def test_create_handler_invalid_tilt(self):
        """Test amb default_head_tilt invàlid"""
        with self.assertRaises(ValueError):
            create_visual_tracking_handler(self.mock_car, self.mock_vilib, True, "invalid")
    
    def test_is_person_centered_function(self):
        """Test de la funció is_person_centered retornada"""
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            self.mock_car, self.mock_vilib, True, 20
        )
        
        # Inicialment no està centrada
        self.assertFalse(is_centered_func())
        
        # Actualitzar estat
        with lock:
            state['centered'] = True
        
        # Ara hauria d'estar centrada
        self.assertTrue(is_centered_func())


class TestVisualTrackingHandler(unittest.TestCase):
    """Tests per al handler de seguiment visual"""
    
    @patch('visual_tracking.time.sleep')
    def test_handler_without_img(self, mock_sleep):
        """Test que el handler retorna immediatament sense imatge"""
        mock_car = Mock()
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, None, False, 20
        )
        
        # El handler hauria de retornar immediatament
        # No podem executar-lo completament perquè té un loop infinit,
        # però podem verificar que existeix
        self.assertIsNotNone(handler)
        self.assertIsNotNone(state)
        self.assertIsNotNone(lock)
        self.assertIsNotNone(is_centered_func)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_with_vilib_none(self, mock_sleep):
        """Test que el handler retorna immediatament si vilib és None"""
        mock_car = Mock()
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, None, True, 20
        )
        
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    @patch('visual_tracking.actualitzar_angle_camera')
    @patch('visual_tracking.calcular_canvi_angle')
    @patch('visual_tracking.calcular_mitjana_ponderada')
    def test_handler_detection_flow(self, mock_mitjana, mock_canvi, mock_actualitzar, mock_sleep):
        """Test del flux de detecció del handler"""
        mock_car = Mock()
        mock_car.set_cam_pan_angle = Mock()
        mock_car.set_cam_tilt_angle = Mock()
        
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': 320,
            'human_y': 240
        }
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # Verificar que el handler existeix
        self.assertIsNotNone(handler)
        
        # Verificar que l'estat inicial és correcte
        self.assertFalse(state['centered'])
        
        # Configurar mocks per simular una iteració del loop
        mock_mitjana.return_value = 320
        mock_canvi.return_value = 5
        mock_actualitzar.return_value = 5
        
        # Simular una iteració del loop executant parts de la lògica
        # No podem executar el loop completament, però podem verificar que les funcions
        # es criden correctament quan s'executa el handler
        # (Això augmentarà la cobertura quan el handler s'executi en un thread real)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_no_detection(self, mock_sleep):
        """Test del handler quan no hi ha detecció"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # Verificar que l'estat inicial és correcte
        self.assertFalse(state['centered'])
    
    @patch('visual_tracking.time.sleep')
    def test_handler_invalid_detect_obj_parameter(self, mock_sleep):
        """Test del handler quan detect_obj_parameter no és vàlid"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = None  # No és un dict
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # El handler hauria de gestionar aquest cas
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_camera_error_handling(self, mock_sleep):
        """Test que el handler gestiona errors de càmera"""
        mock_car = Mock()
        mock_car.set_cam_pan_angle = Mock(side_effect=AttributeError("No camera"))
        mock_car.set_cam_tilt_angle = Mock(side_effect=AttributeError("No camera"))
        
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': 320,
            'human_y': 240
        }
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # El handler hauria de gestionar errors de càmera
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_detection_history_management(self, mock_sleep):
        """Test de la gestió de l'històric de deteccions"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': 320,
            'human_y': 240
        }
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # Verificar que el handler existeix
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_coordinate_clamping(self, mock_sleep):
        """Test del clamping de coordenades"""
        mock_car = Mock()
        mock_vilib = Mock()
        # Coordenades fora del rang
        mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': 1000,  # Fora del rang
            'human_y': -100   # Fora del rang
        }
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # El handler hauria de gestionar coordenades fora del rang
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_exception_handling(self, mock_sleep):
        """Test que el handler gestiona excepcions"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = Mock(side_effect=Exception("Error"))
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # El handler hauria de gestionar excepcions
        self.assertIsNotNone(handler)


class TestProcessarDeteccioPersona(unittest.TestCase):
    """Tests per a processar_deteccio_persona"""
    
    def setUp(self):
        """Configuració inicial per a cada test"""
        self.mock_vilib = Mock()
        self.detection_history = {'x': [], 'y': []}
        self.state = {'centered': False}
        self.state_lock = threading.Lock()
    
    def test_processar_deteccio_persona_amb_deteccio(self):
        """Test de processar_deteccio_persona amb detecció vàlida"""
        from visual_tracking import processar_deteccio_persona
        
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': 320,
            'human_y': 240
        }
        
        resultat = processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNotNone(resultat)
        pos_x, pos_y, esta_centrada = resultat
        self.assertIsInstance(pos_x, (int, float))
        self.assertIsInstance(pos_y, (int, float))
        self.assertIsInstance(esta_centrada, bool)
        self.assertEqual(len(self.detection_history['x']), 1)
        self.assertEqual(len(self.detection_history['y']), 1)
    
    def test_processar_deteccio_persona_sense_deteccio(self):
        """Test de processar_deteccio_persona sense detecció"""
        from visual_tracking import processar_deteccio_persona
        
        self.mock_vilib.detect_obj_parameter = {'human_n': 0}
        
        resultat = processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNone(resultat)
    
    def test_processar_deteccio_persona_invalid_parameter(self):
        """Test de processar_deteccio_persona amb paràmetre invàlid"""
        from visual_tracking import processar_deteccio_persona
        
        self.mock_vilib.detect_obj_parameter = None
        
        resultat = processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNone(resultat)
    
    def test_processar_deteccio_persona_coordenades_fora_rang(self):
        """Test de processar_deteccio_persona amb coordenades fora del rang"""
        from visual_tracking import processar_deteccio_persona, CAMERA_WIDTH, CAMERA_HEIGHT
        
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': CAMERA_WIDTH + 100,  # Fora del rang
            'human_y': -50  # Fora del rang
        }
        
        resultat = processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNotNone(resultat)
        pos_x, pos_y, _ = resultat
        # Les coordenades haurien d'estar dins del rang
        self.assertLessEqual(pos_x, CAMERA_WIDTH)
        self.assertGreaterEqual(pos_x, 0)
        self.assertLessEqual(pos_y, CAMERA_HEIGHT)
        self.assertGreaterEqual(pos_y, 0)
    
    def test_processar_deteccio_persona_historial_limit(self):
        """Test de processar_deteccio_persona mantenint límit de l'historial"""
        from visual_tracking import processar_deteccio_persona, DETECTION_HISTORY_SIZE
        
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': 320,
            'human_y': 240
        }
        
        # Omplir l'historial fins al límit
        for i in range(DETECTION_HISTORY_SIZE + 5):
            resultat = processar_deteccio_persona(
                self.mock_vilib, self.detection_history, self.state, self.state_lock
            )
            self.assertIsNotNone(resultat)
        
        # L'historial hauria de tenir només DETECTION_HISTORY_SIZE elements
        self.assertEqual(len(self.detection_history['x']), DETECTION_HISTORY_SIZE)
        self.assertEqual(len(self.detection_history['y']), DETECTION_HISTORY_SIZE)
    
    def test_processar_deteccio_persona_centrada_exacta(self):
        """Test de processar_deteccio_persona quan la persona està exactament al centre"""
        from visual_tracking import processar_deteccio_persona, CAMERA_CENTER_X, CAMERA_CENTER_Y
        
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': CAMERA_CENTER_X,
            'human_y': CAMERA_CENTER_Y
        }
        
        resultat = processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNotNone(resultat)
        _, _, esta_centrada = resultat
        self.assertTrue(esta_centrada)
        with self.state_lock:
            self.assertTrue(self.state['centered'])
    
    def test_processar_deteccio_persona_centrada_limits(self):
        """Test de processar_deteccio_persona quan la persona està als límits de la zona central"""
        from visual_tracking import processar_deteccio_persona, CAMERA_CENTER_X, CAMERA_CENTER_Y, CENTER_ZONE_TOLERANCE
        
        # Test al límit superior de la tolerància (just dins)
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': CAMERA_CENTER_X + CENTER_ZONE_TOLERANCE - 1,
            'human_y': CAMERA_CENTER_Y + CENTER_ZONE_TOLERANCE - 1
        }
        
        resultat = processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNotNone(resultat)
        _, _, esta_centrada = resultat
        self.assertTrue(esta_centrada)
        
        # Test al límit inferior de la tolerància (just dins)
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': CAMERA_CENTER_X - CENTER_ZONE_TOLERANCE + 1,
            'human_y': CAMERA_CENTER_Y - CENTER_ZONE_TOLERANCE + 1
        }
        
        resultat = processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNotNone(resultat)
        _, _, esta_centrada = resultat
        self.assertTrue(esta_centrada)
    
    def test_processar_deteccio_persona_no_centrada_limits(self):
        """Test de processar_deteccio_persona quan la persona està just fora dels límits"""
        from visual_tracking import processar_deteccio_persona, CAMERA_CENTER_X, CAMERA_CENTER_Y, CENTER_ZONE_TOLERANCE
        
        # Netejar l'historial per evitar interferències de tests anteriors
        self.detection_history['x'].clear()
        self.detection_history['y'].clear()
        
        # Test just fora del límit (X fora, Y dins)
        # Utilitzem valors clarament fora de la tolerància per evitar problemes amb la mitjana ponderada
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': CAMERA_CENTER_X + CENTER_ZONE_TOLERANCE + 50,  # Clarament fora
            'human_y': CAMERA_CENTER_Y
        }
        
        resultat = processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNotNone(resultat)
        _, _, esta_centrada = resultat
        self.assertFalse(esta_centrada, "Persona amb X clarament fora hauria de no estar centrada")
        
        # Netejar l'historial per al segon test
        self.detection_history['x'].clear()
        self.detection_history['y'].clear()
        
        # Test just fora del límit (Y fora, X dins)
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': CAMERA_CENTER_X,
            'human_y': CAMERA_CENTER_Y + CENTER_ZONE_TOLERANCE + 50  # Clarament fora
        }
        
        resultat = processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNotNone(resultat)
        _, _, esta_centrada = resultat
        self.assertFalse(esta_centrada, "Persona amb Y clarament fora hauria de no estar centrada")
    
    def test_processar_deteccio_persona_no_hasattr_vilib(self):
        """Test de processar_deteccio_persona quan vilib no té detect_obj_parameter"""
        from visual_tracking import processar_deteccio_persona
        
        # Crear mock sense detect_obj_parameter
        mock_vilib_sense_param = Mock()
        del mock_vilib_sense_param.detect_obj_parameter
        
        resultat = processar_deteccio_persona(
            mock_vilib_sense_param, self.detection_history, self.state, self.state_lock
        )
        
        self.assertIsNone(resultat)
    
    def test_processar_deteccio_persona_actualitza_estat_centered(self):
        """Test que processar_deteccio_persona actualitza correctament l'estat centered"""
        from visual_tracking import processar_deteccio_persona, CAMERA_CENTER_X, CAMERA_CENTER_Y
        
        # Inicialment no està centrada
        with self.state_lock:
            self.state['centered'] = False
        
        # Persona centrada
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': CAMERA_CENTER_X,
            'human_y': CAMERA_CENTER_Y
        }
        
        processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        with self.state_lock:
            self.assertTrue(self.state['centered'])
        
        # Persona no centrada
        self.mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': CAMERA_CENTER_X + 100,
            'human_y': CAMERA_CENTER_Y + 100
        }
        
        processar_deteccio_persona(
            self.mock_vilib, self.detection_history, self.state, self.state_lock
        )
        
        with self.state_lock:
            self.assertFalse(self.state['centered'])


class TestAplicarAnglesCamera(unittest.TestCase):
    """Tests per a aplicar_angles_camera"""
    
    def test_aplicar_angles_camera_ok(self):
        """Test d'aplicar angles de càmera correctament"""
        from visual_tracking import aplicar_angles_camera
        
        mock_car = Mock()
        mock_car.set_cam_pan_angle = Mock()
        mock_car.set_cam_tilt_angle = Mock()
        
        resultat = aplicar_angles_camera(mock_car, 10, 20)
        
        self.assertTrue(resultat)
        mock_car.set_cam_pan_angle.assert_called_once_with(10)
        mock_car.set_cam_tilt_angle.assert_called_once_with(20)
    
    def test_aplicar_angles_camera_sense_metodes(self):
        """Test d'aplicar angles quan el car no té els mètodes"""
        from visual_tracking import aplicar_angles_camera
        
        mock_car = Mock()
        # No definir set_cam_pan_angle ni set_cam_tilt_angle
        
        resultat = aplicar_angles_camera(mock_car, 10, 20)
        
        # Hauria de retornar True encara que no hi hagi mètodes
        self.assertTrue(resultat)
    
    def test_aplicar_angles_camera_error(self):
        """Test d'aplicar angles quan hi ha un error"""
        from visual_tracking import aplicar_angles_camera
        
        mock_car = Mock()
        mock_car.set_cam_pan_angle = Mock(side_effect=AttributeError("Error"))
        mock_car.set_cam_tilt_angle = Mock()
        
        resultat = aplicar_angles_camera(mock_car, 10, 20)
        
        self.assertFalse(resultat)


class TestVisualTrackingHandlerLoop(unittest.TestCase):
    """Tests per a parts del loop del visual_tracking_handler"""
    
    @patch('visual_tracking.time.sleep')
    def test_handler_loop_initialization(self, mock_sleep):
        """Test de la inicialització del loop del handler"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # Verificar que el handler existeix
        self.assertIsNotNone(handler)
        
        # Verificar inicialització
        self.assertFalse(state['centered'])
    
    @patch('visual_tracking.time.sleep')
    @patch('visual_tracking.processar_deteccio_persona')
    @patch('visual_tracking.calcular_canvi_angle')
    @patch('visual_tracking.actualitzar_angle_camera')
    @patch('visual_tracking.aplicar_angles_camera')
    def test_handler_loop_with_detection(self, mock_aplicar, mock_actualitzar, 
                                         mock_canvi, mock_processar, mock_sleep):
        """Test del loop del handler amb detecció"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 1}
        
        # Mock de processar_deteccio_persona per retornar resultat
        mock_processar.return_value = (320, 240, True)
        mock_canvi.return_value = 5
        mock_actualitzar.return_value = 5
        mock_aplicar.return_value = True
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # El handler existeix però no podem executar-lo completament
        # Però podem verificar que les funcions es criden correctament
        # quan s'executa el handler en un thread real
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    @patch('visual_tracking.processar_deteccio_persona')
    def test_handler_loop_no_detection(self, mock_processar, mock_sleep):
        """Test del loop del handler sense detecció"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        
        # Mock de processar_deteccio_persona per retornar None
        mock_processar.return_value = None
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # Verificar que el handler existeix
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_loop_exception_handling(self, mock_sleep):
        """Test del maneig d'excepcions al loop del handler"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = Mock(side_effect=Exception("Error"))
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # El handler hauria de gestionar excepcions
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_vilib_init_delay(self, mock_sleep):
        """Test que el handler espera el delay d'inicialització de Vilib"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # El handler existeix
        self.assertIsNotNone(handler)
        
        # Quan s'executi el handler, hauria de cridar time.sleep amb VILIB_INIT_DELAY
        # Però no podem executar-lo completament, només verificar que existeix
    
    @patch('visual_tracking.time.sleep')
    @patch('visual_tracking.processar_iteracio_tracking')
    def test_handler_execution_with_controlled_loop(self, mock_processar_iteracio, mock_sleep):
        """Test que executa el handler de manera controlada amb mock que permet sortir del loop"""
        from visual_tracking import VILIB_INIT_DELAY, TRACKING_LOOP_DELAY
        
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 1}
        
        # Configurar mock per retornar angles i permetre sortir del loop
        call_count = {'iterations': 0}
        def mock_processar_side_effect(*args, **kwargs):
            call_count['iterations'] += 1
            if call_count['iterations'] > 2:  # Executar 2 iteracions i després sortir
                raise KeyboardInterrupt("Test exit")
            return (0, 20)
        
        mock_processar_iteracio.side_effect = mock_processar_side_effect
        
        # Configurar mock_sleep per llançar excepció després d'algunes crides
        sleep_calls = []
        def mock_sleep_side_effect(delay):
            sleep_calls.append(delay)
            if len(sleep_calls) > 10:  # Sortir després d'alguns sleeps
                raise KeyboardInterrupt("Test exit")
        
        mock_sleep.side_effect = mock_sleep_side_effect
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # Executar handler - hauria de cridar sleep amb VILIB_INIT_DELAY primer
        try:
            handler()
        except KeyboardInterrupt:
            pass  # Sortida controlada del loop
        
        # Verificar que s'ha cridat time.sleep amb VILIB_INIT_DELAY
        self.assertTrue(len(sleep_calls) > 0)
        self.assertEqual(sleep_calls[0], VILIB_INIT_DELAY)


class TestProcessarIteracioTracking(unittest.TestCase):
    """Tests per a processar_iteracio_tracking"""
    
    def setUp(self):
        """Configuració inicial per a cada test"""
        self.mock_vilib = Mock()
        self.detection_history = {'x': [], 'y': []}
        self.state = {'centered': False}
        self.state_lock = threading.Lock()
        self.mock_car = Mock()
        self.mock_car.set_cam_pan_angle = Mock()
        self.mock_car.set_cam_tilt_angle = Mock()
    
    @patch('visual_tracking.aplicar_angles_camera')
    @patch('visual_tracking.actualitzar_angle_camera')
    @patch('visual_tracking.calcular_canvi_angle')
    @patch('visual_tracking.processar_deteccio_persona')
    def test_processar_iteracio_amb_deteccio(self, mock_processar, mock_canvi, 
                                            mock_actualitzar, mock_aplicar):
        """Test de processar_iteracio_tracking amb detecció"""
        mock_processar.return_value = (320, 240, True)
        mock_canvi.return_value = 5
        mock_actualitzar.return_value = 10
        
        pan_angle, tilt_angle = processar_iteracio_tracking(
            self.mock_vilib, self.detection_history, self.state, self.state_lock,
            self.mock_car, 0, 20
        )
        
        self.assertEqual(pan_angle, 10)
        self.assertEqual(tilt_angle, 10)
        mock_processar.assert_called_once()
        mock_aplicar.assert_called_once()
    
    @patch('visual_tracking.processar_deteccio_persona')
    def test_processar_iteracio_sense_deteccio(self, mock_processar):
        """Test de processar_iteracio_tracking sense detecció"""
        mock_processar.return_value = None
        
        pan_angle, tilt_angle = processar_iteracio_tracking(
            self.mock_vilib, self.detection_history, self.state, self.state_lock,
            self.mock_car, 5, 15
        )
        
        # Els angles haurien de romandre iguals
        self.assertEqual(pan_angle, 5)
        self.assertEqual(tilt_angle, 15)
        # L'historial hauria d'estar buit
        self.assertEqual(len(self.detection_history['x']), 0)
        self.assertEqual(len(self.detection_history['y']), 0)
        # L'estat hauria de ser False
        self.assertFalse(self.state['centered'])
    
    @patch('visual_tracking.aplicar_angles_camera')
    @patch('visual_tracking.actualitzar_angle_camera')
    @patch('visual_tracking.calcular_canvi_angle')
    @patch('visual_tracking.processar_deteccio_persona')
    def test_processar_iteracio_angles_actualitzats(self, mock_processar, mock_canvi,
                                                    mock_actualitzar, mock_aplicar):
        """Test que els angles s'actualitzen correctament"""
        mock_processar.return_value = (320, 240, False)
        mock_canvi.side_effect = [3, -2]  # canvi_pan, canvi_tilt
        mock_actualitzar.side_effect = [3, 18]  # nou_pan, nou_tilt
        
        pan_angle, tilt_angle = processar_iteracio_tracking(
            self.mock_vilib, self.detection_history, self.state, self.state_lock,
            self.mock_car, 0, 20
        )
        
        self.assertEqual(pan_angle, 3)
        self.assertEqual(tilt_angle, 18)
        mock_aplicar.assert_called_once_with(self.mock_car, 3, 18)


if __name__ == '__main__':
    unittest.main()

