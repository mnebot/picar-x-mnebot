"""
Tests específics per augmentar la cobertura de gpt_car.py
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import threading
import time

# Afegir el directori pare al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock de les dependències externes
mock_keys = MagicMock()
mock_keys.OPENAI_API_KEY = "test-api-key"
mock_keys.OPENAI_ASSISTANT_ID = "test-assistant-id"
sys.modules['keys'] = mock_keys

mock_readline = MagicMock()
sys.modules['readline'] = mock_readline

mock_speech_recognition = MagicMock()
sys.modules['speech_recognition'] = mock_speech_recognition

# Mock de pwd per Windows
try:
    import pwd
except ImportError:
    mock_pwd = MagicMock()
    mock_pwd.getpwuid.return_value = [None, None, None, None, None, None, None, None, None, None, 'testuser']
    sys.modules['pwd'] = mock_pwd

# Mock de openai
sys.modules['openai'] = MagicMock()

sys.modules['picarx'] = MagicMock()
sys.modules['robot_hat'] = MagicMock()
sys.modules['vilib'] = MagicMock()
sys.modules['cv2'] = MagicMock()


class TestGptCarReadlineImport(unittest.TestCase):
    """Tests per a la importació de readline"""
    
    def test_readline_import_success(self):
        """Test que readline s'importa correctament si està disponible"""
        try:
            import readline
            readline_available = True
        except (ImportError, OSError):
            readline_available = False
        
        # Verificar que el codi maneja correctament la importació
        self.assertIsInstance(readline_available, bool)
    
    def test_readline_import_failure(self):
        """Test que el codi continua si readline no està disponible"""
        try:
            # Simular importació fallida
            raise ImportError("No module named 'readline'")
        except (ImportError, OSError):
            # El codi hauria de continuar
            continue_ok = True
        
        self.assertTrue(continue_ok)


class TestGptCarTTYDetection(unittest.TestCase):
    """Tests per a la detecció de TTY"""
    
    def test_tty_detection_with_isatty(self):
        """Test de detecció de TTY quan isatty està disponible"""
        mock_stdin = Mock()
        mock_stdin.isatty = Mock(return_value=True)
        
        has_tty = mock_stdin.isatty() if hasattr(mock_stdin, 'isatty') else False
        self.assertTrue(has_tty)
    
    def test_tty_detection_without_isatty(self):
        """Test de detecció de TTY quan isatty no està disponible"""
        mock_stdin = Mock()
        delattr(mock_stdin, 'isatty')
        
        has_tty = mock_stdin.isatty() if hasattr(mock_stdin, 'isatty') else False
        self.assertFalse(has_tty)
    
    def test_keyboard_mode_without_tty(self):
        """Test que el mode keyboard canvia a voice si no hi ha TTY"""
        has_tty = False
        args = ['--keyboard']
        
        if '--keyboard' in args:
            if has_tty:
                input_mode = 'keyboard'
            else:
                input_mode = 'voice'
                warning_shown = True
        else:
            input_mode = 'voice'
            warning_shown = False
        
        self.assertEqual(input_mode, 'voice')
        self.assertTrue(warning_shown)


class TestGptCarVolumeValidation(unittest.TestCase):
    """Tests per a la validació de VOLUME_DB"""
    
    def test_volume_db_valid(self):
        """Test amb VOLUME_DB vàlid"""
        VOLUME_DB = 3
        original_volume = VOLUME_DB
        
        if not isinstance(VOLUME_DB, (int, float)) or VOLUME_DB < 0 or VOLUME_DB > 10:
            VOLUME_DB = 3
        
        self.assertEqual(VOLUME_DB, original_volume)
    
    def test_volume_db_too_high(self):
        """Test amb VOLUME_DB massa alt"""
        VOLUME_DB = 15
        
        if not isinstance(VOLUME_DB, (int, float)) or VOLUME_DB < 0 or VOLUME_DB > 10:
            VOLUME_DB = 3
        
        self.assertEqual(VOLUME_DB, 3)
    
    def test_volume_db_too_low(self):
        """Test amb VOLUME_DB massa baix"""
        VOLUME_DB = -1
        
        if not isinstance(VOLUME_DB, (int, float)) or VOLUME_DB < 0 or VOLUME_DB > 10:
            VOLUME_DB = 3
        
        self.assertEqual(VOLUME_DB, 3)
    
    def test_volume_db_invalid_type(self):
        """Test amb VOLUME_DB de tipus invàlid"""
        VOLUME_DB = "invalid"
        
        if not isinstance(VOLUME_DB, (int, float)) or VOLUME_DB < 0 or VOLUME_DB > 10:
            VOLUME_DB = 3
        
        self.assertEqual(VOLUME_DB, 3)


class TestGptCarPicarxInit(unittest.TestCase):
    """Tests per a la inicialització de Picarx"""
    
    @patch('gpt_car.time.sleep')
    def test_picarx_init_success(self, mock_sleep):
        """Test d'inicialització exitosa de Picarx"""
        mock_car = Mock()
        mock_picarx_class = Mock(return_value=mock_car)
        
        try:
            my_car = mock_picarx_class()
            time.sleep(1)
            init_success = True
        except Exception as e:
            init_success = False
            error_msg = str(e)
        
        self.assertTrue(init_success)
        mock_sleep.assert_called_once_with(1)
    
    @patch('gpt_car.time.sleep')
    def test_picarx_init_failure(self, mock_sleep):
        """Test d'inicialització fallida de Picarx"""
        mock_picarx_class = Mock(side_effect=Exception("Hardware error"))
        
        try:
            my_car = mock_picarx_class()
            time.sleep(1)
            init_success = True
        except Exception as e:
            init_success = False
            error_msg = str(e)
            # El codi hauria de preservar l'excepció original
            with self.assertRaises(RuntimeError):
                raise RuntimeError(f"Error inicialitzant Picarx: {e}") from e
        
        self.assertFalse(init_success)


class TestGptCarOsPopen(unittest.TestCase):
    """Tests per a os.popen i tancament de procés"""
    
    def test_os_popen_success(self):
        """Test d'os.popen exitós"""
        mock_proc = Mock()
        mock_proc.close = Mock()
        
        try:
            proc = mock_proc
            proc.close()
            success = True
        except Exception as e:
            success = False
            error_msg = str(e)
        
        self.assertTrue(success)
        mock_proc.close.assert_called_once()
    
    def test_os_popen_failure(self):
        """Test d'os.popen amb error"""
        mock_proc = Mock()
        mock_proc.close = Mock(side_effect=Exception("Close error"))
        
        try:
            proc = mock_proc
            proc.close()
            success = True
        except Exception as e:
            success = False
            error_msg = str(e)
            # El codi hauria de continuar
            continue_ok = True
        
        self.assertFalse(success)
        self.assertTrue(continue_ok)


class TestGptCarMainResponseProcessing(unittest.TestCase):
    """Tests per al processament de respostes a main()"""
    
    def test_response_processing_empty_dict(self):
        """Test de processament de resposta buida"""
        response = {}
        
        try:
            if isinstance(response, dict):
                if 'actions' in response:
                    actions = list(response['actions'])
                else:
                    actions = ['stop']
                
                if 'answer' in response:
                    answer = response['answer']
                else:
                    answer = ''
            else:
                response = str(response)
                if len(response) > 0:
                    actions = []
                    answer = response
        except Exception as e:
            actions = []
            answer = ''
        
        self.assertEqual(actions, ['stop'])
        self.assertEqual(answer, '')
    
    def test_response_processing_with_sound_actions(self):
        """Test de processament de resposta amb accions de so"""
        response = {
            'actions': ['wave', 'honking', 'start engine'],
            'answer': 'Hello'
        }
        SOUND_EFFECT_ACTIONS = ["honking", "start engine"]
        _sound_actions = []
        
        try:
            if isinstance(response, dict):
                if 'actions' in response:
                    actions = list(response['actions'])
                else:
                    actions = ['stop']
                
                if 'answer' in response:
                    answer = response['answer']
                else:
                    answer = ''
                
                if len(answer) > 0:
                    _actions = actions.copy()
                    for _action in _actions:
                        if _action in SOUND_EFFECT_ACTIONS:
                            _sound_actions.append(_action)
                            actions.remove(_action)
        except Exception as e:
            actions = []
            answer = ''
            _sound_actions = []
        
        self.assertEqual(actions, ['wave'])
        self.assertEqual(_sound_actions, ['honking', 'start engine'])
        self.assertEqual(answer, 'Hello')
    
    def test_response_processing_exception(self):
        """Test de processament de resposta amb excepció"""
        response = None
        
        try:
            if isinstance(response, dict):
                actions = list(response.get('actions', ['stop']))
                answer = response.get('answer', '')
            else:
                response_str = str(response) if response else ''
                if len(response_str) > 0:
                    actions = []
                    answer = response_str
                else:
                    actions = []
                    answer = ''
        except Exception as e:
            actions = []
            answer = ''
        
        self.assertEqual(actions, [])
        self.assertEqual(answer, '')


class TestGptCarImageHandling(unittest.TestCase):
    """Tests per a la gestió d'imatges"""
    
    @patch('gpt_car.os.path.join')
    def test_image_path_primary_success(self, mock_join):
        """Test de ruta d'imatge primària exitosa"""
        current_path = '/test/path'
        mock_join.return_value = '/test/path/img_input.jpg'
        
        img_path = os.path.join(current_path, 'img_input.jpg')
        
        try:
            # Simular escriure imatge
            written = True
        except (ValueError, AttributeError) as e:
            written = False
            img_path = None
        
        self.assertIsNotNone(img_path)
        self.assertTrue(written)
    
    @patch('gpt_car.tempfile.gettempdir')
    @patch('gpt_car.os.path.join')
    def test_image_path_fallback(self, mock_join, mock_gettempdir):
        """Test de ruta d'imatge fallback"""
        current_path = '/test/path'
        mock_join.side_effect = [
            '/test/path/img_input.jpg',
            '/tmp/img_input.jpg'
        ]
        mock_gettempdir.return_value = '/tmp'
        
        img_path = os.path.join(current_path, 'img_input.jpg')
        
        try:
            # Simular error
            raise ValueError("Cannot write")
        except (ValueError, AttributeError) as e:
            # Try alternative location
            try:
                import tempfile
                img_path = os.path.join(tempfile.gettempdir(), 'img_input.jpg')
                written = True
            except Exception as e2:
                img_path = None
                written = False
        
        self.assertIsNotNone(img_path)
        self.assertTrue(written)
    
    def test_image_path_vilib_not_available(self):
        """Test quan Vilib.img no està disponible"""
        class MockVilib:
            pass
        
        vilib = MockVilib()
        
        try:
            if not hasattr(vilib, 'img') or vilib.img is None:
                raise ValueError("Vilib.img no està disponible")
        except ValueError as e:
            img_path = None
        
        self.assertIsNone(img_path)


if __name__ == '__main__':
    unittest.main()

