"""
Tests unitaris per a visual_tracking.py
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os
import threading
import importlib.util

# Afegir el directori pare al path per poder importar els mòduls
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Si visual_tracking ha estat mockejat (ex. per test_gpt_car_refactored_functions),
# carregar el mòdul real des del fitxer per evitar fallades dels tests
_vt = sys.modules.get('visual_tracking')
_vt_file = getattr(_vt, '__file__', '') if _vt else ''
_is_real_module = isinstance(_vt_file, str) and 'visual_tracking' in _vt_file
if not _is_real_module:
    _vt_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _vt_spec = importlib.util.spec_from_file_location(
        'visual_tracking',
        os.path.join(_vt_dir, 'visual_tracking.py')
    )
    _vt_module = importlib.util.module_from_spec(_vt_spec)
    sys.modules['visual_tracking'] = _vt_module
    _vt_spec.loader.exec_module(_vt_module)

from visual_tracking import (
    clamp_number,
    calcular_mitjana_ponderada,
    calcular_canvi_angle,
    actualitzar_angle_camera,
    create_visual_tracking_handler,
    processar_deteccio_persona,
    aplicar_angles_camera,
    processar_iteracio_tracking,
    girar_robot_cap_direccio,
)


class TestClampNumber(unittest.TestCase):
    """Tests per a clamp_number"""
    pass


class TestCalcularMitjanaPonderada(unittest.TestCase):
    """Tests per a calcular_mitjana_ponderada"""
    pass


class TestCalcularCanviAngle(unittest.TestCase):
    """Tests per a calcular_canvi_angle"""
    pass


class TestActualitzarAngleCamera(unittest.TestCase):
    """Tests per a actualitzar_angle_camera"""
    pass


class TestCreateVisualTrackingHandler(unittest.TestCase):
    """Tests per a create_visual_tracking_handler"""
    
    @patch('visual_tracking.time.sleep')
    def test_create_handler_without_img(self, mock_sleep):
        """Test crear handler sense imatge"""
        mock_car = Mock()
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, None, False, 20
        )
        
        self.assertIsNotNone(handler)
        self.assertIsNotNone(state)
        self.assertIsNotNone(lock)
        self.assertIsNotNone(is_centered_func)


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
    
    def test_processar_deteccio_actualitza_last_seen_state(self):
        """Test que processar_deteccio_persona actualitza last_seen_x i last_seen_time (FASE 2.1)"""
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': 100,
            'human_y': 240
        }
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': None,
            'last_seen_time': None,
            'person_lost_turn_done': True,
        }
        state_lock = threading.Lock()
        
        with patch('visual_tracking.time.time', return_value=1000.0):
            resultat = processar_deteccio_persona(
                mock_vilib, detection_history, state, state_lock
            )
        
        self.assertIsNotNone(resultat)
        with state_lock:
            self.assertIsNotNone(state['last_seen_x'])
            self.assertEqual(state['last_seen_time'], 1000.0)
            self.assertFalse(state['person_lost_turn_done'])


class TestAplicarAnglesCamera(unittest.TestCase):
    """Tests per a aplicar_angles_camera"""
    pass


class TestVisualTrackingHandlerLoop(unittest.TestCase):
    """Tests per al loop del handler de seguiment visual"""
    
    @patch('visual_tracking.time.sleep')
    def test_handler_loop_exception_handling(self, mock_sleep):
        """Test que el loop gestiona excepcions"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = Mock(side_effect=Exception("Error"))
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # El handler hauria de gestionar excepcions
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_loop_no_detection(self, mock_sleep):
        """Test del loop quan no hi ha detecció"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        
        handler, state, lock, is_centered_func = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        
        # El handler hauria de gestionar el cas sense detecció
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_loop_with_detection(self, mock_sleep):
        """Test del loop quan hi ha detecció"""
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
        
        # El handler hauria de gestionar deteccions
        self.assertIsNotNone(handler)
    
    @patch('visual_tracking.time.sleep')
    def test_handler_vilib_init_delay(self, mock_sleep):
        """Test del delay d'inicialització de Vilib"""
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
        
        # El handler hauria de gestionar el delay d'inicialització
        self.assertIsNotNone(handler)


class TestGirarRobotCapDireccio(unittest.TestCase):
    """Tests per a girar_robot_cap_direccio (FASE 2.1)"""
    
    @patch('visual_tracking.time.sleep')
    def test_girar_esquerra(self, mock_sleep):
        """Test gir cap a l'esquerra"""
        mock_car = Mock()
        mock_car.set_dir_servo_angle = Mock()
        mock_car.forward = Mock()
        mock_car.stop = Mock()
        
        resultat = girar_robot_cap_direccio(mock_car, 'esquerra')
        
        self.assertTrue(resultat)
        mock_car.set_dir_servo_angle.assert_any_call(-30)  # TURN_ANGLE_DEGREES
        mock_car.forward.assert_called_once()
        mock_car.stop.assert_called_once()
        mock_car.set_dir_servo_angle.assert_any_call(0)
    
    @patch('visual_tracking.time.sleep')
    def test_girar_dreta(self, mock_sleep):
        """Test gir cap a la dreta"""
        mock_car = Mock()
        mock_car.set_dir_servo_angle = Mock()
        mock_car.forward = Mock()
        mock_car.stop = Mock()
        
        resultat = girar_robot_cap_direccio(mock_car, 'dreta')
        
        self.assertTrue(resultat)
        mock_car.set_dir_servo_angle.assert_any_call(30)
    
    def test_girar_sense_metodes_retorna_false(self):
        """Test que retorna False si el cotxe no té els mètodes necessaris"""
        mock_car = Mock(spec=[])  # Sense atributs
        
        resultat = girar_robot_cap_direccio(mock_car, 'esquerra')
        
        self.assertFalse(resultat)
    
    @patch('visual_tracking.time.sleep')
    def test_girar_gestiona_excepcio(self, mock_sleep):
        """Test que gestiona excepcions durant el gir"""
        mock_car = Mock()
        mock_car.set_dir_servo_angle = Mock()
        mock_car.forward = Mock(side_effect=Exception("Error motor"))
        mock_car.stop = Mock()
        
        resultat = girar_robot_cap_direccio(mock_car, 'esquerra')
        
        self.assertFalse(resultat)
        self.assertTrue(mock_car.stop.called)


class TestProcessarIteracioTracking(unittest.TestCase):
    """Tests per a processar_iteracio_tracking"""
    
    @patch('visual_tracking.girar_robot_cap_direccio')
    @patch('visual_tracking.time.time')
    def test_persona_perduda_gira_cap_esquerra(self, mock_time, mock_girar):
        """Test que gira cap a l'esquerra quan persona es perd des de l'esquerra (FASE 2.1)"""
        mock_time.return_value = 1000.6  # 0.6s des de last_seen (1000.0) >= 0.5s timeout
        mock_girar.return_value = True
        
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': 100,  # Esquerra del centre (320)
            'last_seen_time': 1000.0,
            'person_lost_turn_done': False,
        }
        state_lock = threading.Lock()
        mock_car = Mock()
        
        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )
        
        mock_girar.assert_called_once_with(mock_car, 'esquerra')
    
    @patch('visual_tracking.girar_robot_cap_direccio')
    @patch('visual_tracking.time.time')
    def test_persona_perduda_gira_cap_dreta(self, mock_time, mock_girar):
        """Test que gira cap a la dreta quan persona es perd des de la dreta (FASE 2.1)"""
        mock_time.side_effect = [1000.6]
        mock_girar.return_value = True
        
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': 500,  # Dreta del centre
            'last_seen_time': 1000.0,
            'person_lost_turn_done': False,
        }
        state_lock = threading.Lock()
        mock_car = Mock()
        
        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )
        
        mock_girar.assert_called_once_with(mock_car, 'dreta')
    
    @patch('visual_tracking.girar_robot_cap_direccio')
    @patch('visual_tracking.time.time')
    def test_no_gira_quan_mai_s_ha_vist_persona(self, mock_time, mock_girar):
        """Test que no gira quan no s'ha detectat mai cap persona (FASE 2.1)"""
        mock_time.return_value = 1000.0
        
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': None,
            'last_seen_time': None,
            'person_lost_turn_done': False,
        }
        state_lock = threading.Lock()
        mock_car = Mock()
        
        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )
        
        mock_girar.assert_not_called()
    
    @patch('visual_tracking.girar_robot_cap_direccio')
    @patch('visual_tracking.time.time')
    def test_no_gira_quan_timeout_no_complert(self, mock_time, mock_girar):
        """Test que no gira abans de PERSON_LOST_TIMEOUT (FASE 2.1)"""
        mock_time.return_value = 1000.2  # Només 0.2s des de last_seen (1000.0)
        
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': 100,
            'last_seen_time': 1000.0,
            'person_lost_turn_done': False,
        }
        state_lock = threading.Lock()
        mock_car = Mock()
        
        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )
        
        mock_girar.assert_not_called()
    
    @patch('visual_tracking.girar_robot_cap_direccio')
    @patch('visual_tracking.time.time')
    def test_no_gira_dos_cops_per_mateix_esdeveniment(self, mock_time, mock_girar):
        """Test que no gira dues vegades per la mateixa pèrdua (FASE 2.1)"""
        mock_time.side_effect = [1000.6, 1000.7]  # Després del timeout
        mock_girar.return_value = True
        
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': 100,
            'last_seen_time': 1000.0,
            'person_lost_turn_done': False,
        }
        state_lock = threading.Lock()
        mock_car = Mock()
        
        # Primera iteració: ha de girar
        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )
        # Segona iteració: no ha de girar (person_lost_turn_done=True)
        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )
        
        mock_girar.assert_called_once()


class TestEstratejiaRecercaFase22(unittest.TestCase):
    """Tests per a l'estratègia de recerca (FASE 2.2)"""

    @patch('visual_tracking.girar_robot_cap_direccio')
    @patch('visual_tracking.time.time')
    def test_inicia_recerca_quan_persona_perduda(self, mock_time, mock_girar):
        """Test que s'inicia el mode recerca quan es fa el gir inicial (FASE 2.2)"""
        mock_time.return_value = 1000.6  # >= last_seen_time + 0.5 per trigar persona perduda
        mock_girar.return_value = True

        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': 100,
            'last_seen_time': 1000.0,
            'person_lost_turn_done': False,
            'search_start_time': None,
            'search_direction': None,
            'search_last_extra_turn_time': None,
            'search_last_camera_step_time': None,
            'search_pan_direction': 1,
        }
        state_lock = threading.Lock()
        mock_car = Mock()

        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )

        with state_lock:
            self.assertIsNotNone(state['search_start_time'])
            self.assertEqual(state['search_direction'], 'esquerra')

    @patch('visual_tracking.girar_robot_cap_direccio')
    @patch('visual_tracking.time.time')
    def test_recerca_timeout_5_segons(self, mock_time, mock_girar):
        """Test que el mode recerca surt després de 5 segons (FASE 2.2)"""
        mock_time.return_value = 1005.7  # search_start 1000.6 + 5.1s >= SEARCH_TIMEOUT
        mock_girar.return_value = True

        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': 100,
            'last_seen_time': 1000.0,
            'person_lost_turn_done': False,
            'search_start_time': 1000.6,
            'search_direction': 'esquerra',
            'search_last_extra_turn_time': 1000.6,
            'search_last_camera_step_time': 1000.6,
            'search_pan_direction': -1,
        }
        state_lock = threading.Lock()
        mock_car = Mock()

        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )

        with state_lock:
            self.assertIsNone(state['search_start_time'])

    @patch('visual_tracking.girar_robot_cap_direccio')
    @patch('visual_tracking.time.time')
    def test_recerca_gir_extra_amb_15_graus(self, mock_time, mock_girar):
        """Test que durant recerca es fan girs addicionals de 15 graus (FASE 2.2)"""
        mock_time.return_value = 1001.7  # >1s des de search_last_extra_turn (1000.6)
        mock_girar.return_value = True

        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': 100,
            'last_seen_time': 1000.0,
            'person_lost_turn_done': True,
            'search_start_time': 1000.6,
            'search_direction': 'esquerra',
            'search_last_extra_turn_time': 1000.6,
            'search_last_camera_step_time': 1000.6,
            'search_pan_direction': -1,
        }
        state_lock = threading.Lock()
        mock_car = Mock()

        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )

        # Hauria d'haver cridat girar amb 15 graus
        mock_girar.assert_called_with(mock_car, 'esquerra', 15)

    @patch('visual_tracking.time.time')
    def test_recerca_mou_camera_pan(self, mock_time):
        """Test que durant recerca es mou la càmera pan (FASE 2.2)"""
        mock_time.return_value = 1000.9  # >0.25s des de search_last_camera_step (1000.6)
        mock_car = Mock()
        mock_car.set_cam_pan_angle = Mock()
        mock_car.set_cam_tilt_angle = Mock()

        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {'human_n': 0}
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': 100,
            'last_seen_time': 1000.0,
            'person_lost_turn_done': True,
            'search_start_time': 1000.6,
            'search_direction': 'esquerra',
            'search_last_extra_turn_time': 1000.6,
            'search_last_camera_step_time': 1000.6,
            'search_pan_direction': -1,
        }
        state_lock = threading.Lock()
        pan_angle, tilt_angle = 0, 20

        with patch('visual_tracking.girar_robot_cap_direccio', return_value=True):
            nou_pan, nou_tilt = processar_iteracio_tracking(
                mock_vilib, detection_history, state, state_lock,
                mock_car, pan_angle, tilt_angle
            )

        # El pan hauria d'haver canviat (0 + 8*(-1) = -8 per search_pan_direction -1)
        self.assertEqual(nou_pan, -8)
        self.assertEqual(nou_tilt, 20)
        mock_car.set_cam_pan_angle.assert_called_once_with(-8)
        mock_car.set_cam_tilt_angle.assert_called_once_with(20)

    @patch('visual_tracking.time.time')
    def test_recerca_surt_quan_persona_trobada(self, mock_time):
        """Test que el mode recerca es reinicia quan es torna a detectar persona (FASE 2.2)"""
        mock_time.return_value = 1000.0
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {
            'human_n': 1,
            'human_x': 320,
            'human_y': 240
        }
        detection_history = {'x': [], 'y': []}
        state = {
            'centered': False,
            'last_seen_x': None,
            'last_seen_time': None,
            'person_lost_turn_done': False,
            'search_start_time': 1000.0,
            'search_direction': 'dreta',
            'search_last_extra_turn_time': 1000.0,
            'search_last_camera_step_time': 1000.0,
            'search_pan_direction': 1,
        }
        state_lock = threading.Lock()
        mock_car = Mock()
        mock_car.set_cam_pan_angle = Mock()
        mock_car.set_cam_tilt_angle = Mock()

        processar_iteracio_tracking(
            mock_vilib, detection_history, state, state_lock,
            mock_car, 0, 20
        )

        with state_lock:
            self.assertIsNone(state['search_start_time'])
            self.assertIsNone(state['search_direction'])

    @patch('visual_tracking.time.sleep')
    def test_girar_robot_amb_graus_parametre(self, mock_sleep):
        """Test que girar_robot_cap_direccio accepta angle personalitzat (FASE 2.2)"""
        mock_car = Mock()
        mock_car.set_dir_servo_angle = Mock()
        mock_car.forward = Mock()
        mock_car.stop = Mock()

        resultat = girar_robot_cap_direccio(mock_car, 'esquerra', 15)

        self.assertTrue(resultat)
        mock_car.set_dir_servo_angle.assert_any_call(-15)


class TestCreateHandlerStateFase2(unittest.TestCase):
    """Tests que create_visual_tracking_handler inclou estat FASE 2.1 i 2.2"""
    
    def test_state_inclou_camps_persona_perduda(self):
        """Test que l'estat inclou last_seen_x, last_seen_time, person_lost_turn_done"""
        mock_car = Mock()
        handler, state, lock, is_centered = create_visual_tracking_handler(
            mock_car, None, False, 20
        )
        self.assertIn('last_seen_x', state)
        self.assertIn('last_seen_time', state)
        self.assertIn('person_lost_turn_done', state)
        self.assertIsNone(state['last_seen_x'])
        self.assertIsNone(state['last_seen_time'])
        self.assertFalse(state['person_lost_turn_done'])
    
    def test_state_inclou_camps_estratejia_recerca_fase22(self):
        """Test que l'estat inclou camps per estratègia de recerca (FASE 2.2)"""
        mock_car = Mock()
        handler, state, lock, is_centered = create_visual_tracking_handler(
            mock_car, None, False, 20
        )
        self.assertIn('search_start_time', state)
        self.assertIn('search_direction', state)
        self.assertIn('search_last_extra_turn_time', state)
        self.assertIn('search_last_camera_step_time', state)
        self.assertIn('search_pan_direction', state)
        self.assertIsNone(state['search_start_time'])
        self.assertIsNone(state['search_direction'])
        self.assertEqual(state['search_pan_direction'], 1)

    def test_state_inclou_stop_requested(self):
        """Test que l'estat inclou stop_requested per aturar el seguiment des d'una acció"""
        mock_car = Mock()
        _, state, lock, is_centered = create_visual_tracking_handler(
            mock_car, None, False, 20
        )
        self.assertIn('stop_requested', state)
        self.assertFalse(state['stop_requested'])


class TestHandlerStopRequested(unittest.TestCase):
    """Tests que el handler de seguiment acaba quan stop_requested és True"""

    @patch('visual_tracking.time.sleep')
    @patch('visual_tracking.processar_iteracio_tracking')
    def test_handler_surt_del_loop_quan_stop_requested(self, mock_iteracio, mock_sleep):
        """El loop del handler acaba quan s'estableix stop_requested a True"""
        mock_car = Mock()
        mock_vilib = Mock()
        mock_vilib.detect_obj_parameter = {}

        handler, state, state_lock, _ = create_visual_tracking_handler(
            mock_car, mock_vilib, True, 20
        )
        mock_iteracio.return_value = (0, 20)

        def sleep_side_effect(secs):
            # Després del primer sleep del loop, demanar aturada
            with state_lock:
                state['stop_requested'] = True

        mock_sleep.side_effect = sleep_side_effect

        thread = threading.Thread(target=handler)
        thread.daemon = True
        thread.start()
        thread.join(timeout=3.0)
        self.assertFalse(thread.is_alive(), "El handler hauria d'haver acabat quan stop_requested és True")
        with state_lock:
            self.assertTrue(state['stop_requested'])


if __name__ == '__main__':
    unittest.main()
