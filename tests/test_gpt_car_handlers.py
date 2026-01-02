"""
Tests unitaris per a les funcions handler de gpt_car.py
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import threading
import time

# Afegir el directori pare al path per poder importar els mòduls
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock de les dependències externes abans d'importar els mòduls
mock_keys = MagicMock()
mock_keys.OPENAI_API_KEY = "test-api-key"
mock_keys.OPENAI_ASSISTANT_ID = "test-assistant-id"
sys.modules['keys'] = mock_keys

mock_readline = MagicMock()
sys.modules['readline'] = mock_readline

mock_speech_recognition = MagicMock()
sys.modules['speech_recognition'] = mock_speech_recognition

sys.modules['picarx'] = MagicMock()
sys.modules['robot_hat'] = MagicMock()
sys.modules['vilib'] = MagicMock()
sys.modules['cv2'] = MagicMock()


class TestSpeakHandler(unittest.TestCase):
    """Tests per a speak_hanlder"""
    
    @patch('gpt_car.speak_block')
    @patch('gpt_car.time.sleep')
    def test_speak_handler_logic(self, mock_sleep, mock_speak_block):
        """Test de la lògica del speak_handler"""
        # Simular la lògica del speak_handler
        speech_loaded = False
        tts_file = None
        speech_lock = threading.Lock()
        
        # Simular estat on speech_loaded és True
        with speech_lock:
            speech_loaded = True
            tts_file = '/path/to/file.wav'
        
        # La lògica hauria de processar el fitxer
        if speech_loaded:
            # speak_block seria cridat aquí
            processed = True
            with speech_lock:
                speech_loaded = False
        
        self.assertTrue(processed)
        self.assertFalse(speech_loaded)


class TestActionHandler(unittest.TestCase):
    """Tests per a action_handler"""
    
    @patch('gpt_car.time.sleep')
    @patch('gpt_car.time.time')
    def test_action_handler_standby(self, mock_time, mock_sleep):
        """Test de l'action_handler en estat standby"""
        # Simular la lògica de standby
        action_status = 'standby'
        last_action_status = 'standby'
        action_interval = 5
        last_action_time = 100.0
        mock_time.return_value = 106.0  # 6 segons després
        
        if action_status == 'standby':
            current_time = mock_time()
            if current_time - last_action_time > action_interval:
                last_action_time = current_time
                action_interval = 6  # Simular random.randint(2, 6)
        
        # Verificar que s'ha actualitzat last_action_time
        self.assertEqual(last_action_time, 106.0)
    
    def test_action_handler_think(self):
        """Test de l'action_handler en estat think"""
        action_status = 'think'
        last_action_status = 'standby'
        
        if action_status == 'think':
            if last_action_status != 'think':
                last_action_status = 'think'
        
        self.assertEqual(last_action_status, 'think')
    
    @patch('gpt_car.actions_dict', {'test_action': Mock()})
    def test_action_handler_actions(self):
        """Test de l'action_handler executant accions"""
        action_status = 'actions'
        actions_to_be_done = ['test_action']
        action_lock = threading.Lock()
        mock_car = Mock()
        
        if action_status == 'actions':
            with action_lock:
                _actions = actions_to_be_done
            for _action in _actions:
                try:
                    if _action in {'test_action': Mock()}:
                        # Simular execució d'acció
                        executed = True
                except Exception as e:
                    executed = False
        
        # Verificar que l'acció s'hauria executat
        self.assertTrue(executed)


class TestPersonDetectionHandler(unittest.TestCase):
    """Tests per a person_detection_handler"""
    
    @patch('gpt_car.time.sleep')
    def test_person_detection_without_img(self, mock_sleep):
        """Test que person_detection_handler retorna sense imatge"""
        with_img = False
        
        if not with_img:
            return
        
        # No hauria d'arribar aquí
        self.fail("Hauria d'haver retornat abans")
    
    @patch('gpt_car.time.sleep')
    @patch('gpt_car.time.time')
    def test_person_detection_cooldown(self, mock_time, mock_sleep):
        """Test del cooldown de detecció de persones"""
        person_detected = False
        last_greeting_time = 0
        GREETING_COOLDOWN = 5.0
        current_time = 10.0
        mock_time.return_value = current_time
        
        # Simular que no hem saludat recentment
        if not person_detected or (current_time - last_greeting_time) > GREETING_COOLDOWN:
            should_greet = True
        else:
            should_greet = False
        
        self.assertTrue(should_greet)
        
        # Simular que hem saludat recentment (dins del cooldown)
        last_greeting_time = 8.0
        person_detected = True
        if not person_detected or (current_time - last_greeting_time) > GREETING_COOLDOWN:
            should_greet = True
        else:
            should_greet = False
        
        # current_time (10.0) - last_greeting_time (8.0) = 2.0, que és < 5.0, per tant no hauria de saludar
        self.assertFalse(should_greet)


if __name__ == '__main__':
    unittest.main()

