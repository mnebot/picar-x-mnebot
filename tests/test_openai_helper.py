"""
Tests unitaris per a openai_helper.py
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import sys
import os

# Mock de les dependències externes abans d'importar el mòdul
# Necessari perquè openai_helper importa openai a nivell de mòdul
mock_openai = MagicMock()
sys.modules['openai'] = mock_openai

# Afegir el directori pare al path per poder importar els mòduls
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai_helper import OpenAiHelper, chat_print


class TestChatPrint(unittest.TestCase):
    """Tests per a la funció chat_print"""
    
    @patch('openai_helper.time.time')
    @patch('builtins.print')
    def test_chat_print(self, mock_print, mock_time):
        """Test que chat_print imprimeix correctament"""
        mock_time.return_value = 1234.567
        chat_print("test", "Hello")
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn("1234.567", call_args)
        self.assertIn("test", call_args)
        self.assertIn("Hello", call_args)


class TestOpenAiHelper(unittest.TestCase):
    """Tests per a la classe OpenAiHelper"""
    
    def setUp(self):
        """Configuració inicial per a cada test"""
        self.api_key = "test-api-key"
        self.assistant_id = "test-assistant-id"
        self.assistant_name = "test-assistant"
        
        # Mock del client OpenAI
        self.mock_client = Mock()
        self.mock_thread = Mock()
        self.mock_thread.id = "test-thread-id"
        self.mock_run = Mock()
        self.mock_run.status = "completed"
        
        self.mock_client.beta.threads.create.return_value = self.mock_thread
        # Crear un nou mock per cada test per evitar que es comparteixi l'estat
        self.mock_client.beta.threads.runs.create_and_poll = Mock(return_value=self.mock_run)
    
    @patch('openai_helper.OpenAI')
    def test_init(self, mock_openai):
        """Test de inicialització de OpenAiHelper"""
        mock_openai.return_value = self.mock_client
        
        helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
        
        self.assertEqual(helper.api_key, self.api_key)
        self.assertEqual(helper.assistant_id, self.assistant_id)
        self.assertEqual(helper.assistant_name, self.assistant_name)
        mock_openai.assert_called_once_with(api_key=self.api_key, timeout=30)
    
    def test_prepare_message_with_language(self):
        """Test de _prepare_message_with_language"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            result = helper._prepare_message_with_language("Hola")
            self.assertEqual(result, "Respon sempre en català. Hola")
    
    def test_parse_response_value_json(self):
        """Test de _parse_response_value amb JSON vàlid"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            json_str = '{"actions": ["wave"], "answer": "Hello"}'
            result = helper._parse_response_value(json_str)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["actions"], ["wave"])
            self.assertEqual(result["answer"], "Hello")
    
    def test_parse_response_value_string(self):
        """Test de _parse_response_value amb string no JSON"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            result = helper._parse_response_value("Hello world")
            self.assertEqual(result, "Hello world")
    
    def test_parse_response_value_invalid_json(self):
        """Test de _parse_response_value amb JSON invàlid"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            result = helper._parse_response_value("{invalid json}")
            self.assertEqual(result, "{invalid json}")
    
    def test_parse_response_value_type_error(self):
        """Test de _parse_response_value amb TypeError"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            # Passar None hauria de causar TypeError
            result = helper._parse_response_value(None)
            self.assertEqual(result, "None")
    
    @patch('openai_helper.chat_print')
    def test_process_run_response_completed(self, mock_chat_print):
        """Test de _process_run_response quan el run està completat"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock de la resposta del run
            mock_message = Mock()
            mock_message.role = 'assistant'
            mock_block = Mock()
            mock_block.type = 'text'
            mock_block.text.value = '{"test": "value"}'
            mock_message.content = [mock_block]
            
            mock_messages = Mock()
            mock_messages.data = [mock_message]
            self.mock_client.beta.threads.messages.list.return_value = mock_messages
            
            self.mock_run.status = 'completed'
            result = helper._process_run_response(self.mock_run)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result["test"], "value")
    
    def test_process_run_response_not_completed(self):
        """Test de _process_run_response quan el run no està completat"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            self.mock_run.status = 'failed'
            result = helper._process_run_response(self.mock_run)
            
            self.assertIsNone(result)
    
    @patch('openai_helper.chat_print')
    def test_dialogue(self, mock_chat_print):
        """Test del mètode dialogue"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # El __init__ ja ha cridat create_and_poll una vegada, per tant resetegem el comptador
            initial_call_count = self.mock_client.beta.threads.runs.create_and_poll.call_count
            self.mock_client.beta.threads.messages.create.reset_mock()
            
            # Mock de la resposta
            mock_message = Mock()
            mock_message.role = 'assistant'
            mock_block = Mock()
            mock_block.type = 'text'
            mock_block.text.value = '{"answer": "Hello"}'
            mock_message.content = [mock_block]
            
            mock_messages = Mock()
            mock_messages.data = [mock_message]
            self.mock_client.beta.threads.messages.list.return_value = mock_messages
            
            result = helper.dialogue("Hola")
            
            self.assertIsInstance(result, dict)
            # Verificar que messages.create s'ha cridat una vegada (per dialogue, el de __init__ no crida messages.create)
            self.mock_client.beta.threads.messages.create.assert_called_once()
            # Verificar que create_and_poll s'ha cridat una vegada més (la del dialogue)
            self.assertEqual(self.mock_client.beta.threads.runs.create_and_poll.call_count, initial_call_count + 1)
    
    @patch('openai_helper.chat_print')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake image data')
    def test_dialogue_with_img(self, mock_file, mock_chat_print):
        """Test del mètode dialogue_with_img"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock del fitxer creat
            mock_img_file = Mock()
            mock_img_file.id = "test-file-id"
            self.mock_client.files.create.return_value = mock_img_file
            
            # Mock de la resposta
            mock_message = Mock()
            mock_message.role = 'assistant'
            mock_block = Mock()
            mock_block.type = 'text'
            mock_block.text.value = '{"answer": "Hello with image"}'
            mock_message.content = [mock_block]
            
            mock_messages = Mock()
            mock_messages.data = [mock_message]
            self.mock_client.beta.threads.messages.list.return_value = mock_messages
            
            result = helper.dialogue_with_img("Hola", "/tmp/test.jpg")
            
            self.assertIsInstance(result, dict)
            self.mock_client.files.create.assert_called_once()
            self.mock_client.beta.threads.messages.create.assert_called_once()
    
    def test_stt_success(self):
        """Test de stt amb èxit - simplificat per evitar problemes amb imports dinàmics"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock de l'audio
            mock_audio = Mock()
            mock_audio.get_wav_data.return_value = b'fake wav data'
            
            # Mock de la transcripció
            mock_transcript = Mock()
            mock_transcript.text = "Hello world"
            self.mock_client.audio.transcriptions.create.return_value = mock_transcript
            
            # Mock de BytesIO i wave usant sys.modules
            from io import BytesIO
            mock_bytesio_instance = Mock()
            mock_bytesio_instance.name = None
            with patch('io.BytesIO', return_value=mock_bytesio_instance):
                with patch.dict('sys.modules', {'wave': MagicMock()}):
                    result = helper.stt(mock_audio, language='en')
                    self.assertEqual(result, "Hello world")
                    self.mock_client.audio.transcriptions.create.assert_called_once()
    
    def test_stt_failure(self):
        """Test de stt amb fallo"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock de l'audio que llança excepció
            mock_audio = Mock()
            mock_audio.get_wav_data.side_effect = Exception("Audio error")
            
            with patch.dict('sys.modules', {'wave': MagicMock()}):
                result = helper.stt(mock_audio, language='en')
                self.assertFalse(result)
    
    @patch.dict('sys.modules', {'speech_recognition': MagicMock()})
    def test_speech_recognition_stt_success(self):
        """Test de speech_recognition_stt amb èxit"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock del recognizer
            mock_recognizer = Mock()
            mock_recognizer.recognize_whisper_api.return_value = "Hello world"
            
            mock_audio = Mock()
            
            result = helper.speech_recognition_stt(mock_recognizer, mock_audio)
            
            self.assertEqual(result, "Hello world")
            mock_recognizer.recognize_whisper_api.assert_called_once_with(
                mock_audio, api_key=self.api_key
            )
    
    @patch.dict('sys.modules', {'speech_recognition': MagicMock()})
    def test_speech_recognition_stt_failure(self):
        """Test de speech_recognition_stt amb fallo"""
        # Crear un mock de RequestError
        mock_sr = sys.modules['speech_recognition']
        mock_request_error = type('RequestError', (Exception,), {})
        mock_sr.RequestError = mock_request_error
        
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock del recognizer
            mock_recognizer = Mock()
            mock_recognizer.recognize_whisper_api.side_effect = mock_request_error("API error")
            
            mock_audio = Mock()
            
            result = helper.speech_recognition_stt(mock_recognizer, mock_audio)
            
            self.assertFalse(result)
    
    @patch('openai_helper.os.path.exists')
    @patch('openai_helper.os.path.isdir')
    @patch('openai_helper.os.mkdir')
    def test_text_to_speech_success(self, mock_mkdir, mock_isdir, mock_exists):
        """Test de text_to_speech amb èxit"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock del directori existent
            mock_exists.return_value = True
            mock_isdir.return_value = True
            
            # Mock del streaming response amb context manager
            mock_response = Mock()
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_response)
            mock_context.__exit__ = Mock(return_value=None)
            mock_streaming = Mock()
            mock_streaming.with_streaming_response.create.return_value = mock_context
            self.mock_client.audio.speech = mock_streaming
            
            result = helper.text_to_speech("Hello", "/tmp/test.mp3", voice='echo')
            
            self.assertTrue(result)
            mock_streaming.with_streaming_response.create.assert_called_once()
            mock_response.stream_to_file.assert_called_once_with("/tmp/test.mp3")
    
    @patch('openai_helper.os.path.exists')
    @patch('openai_helper.os.path.isdir')
    @patch('openai_helper.os.mkdir')
    def test_text_to_speech_create_dir(self, mock_mkdir, mock_isdir, mock_exists):
        """Test de text_to_speech creant directori"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock del directori no existent
            mock_exists.return_value = False
            
            # Mock del streaming response amb context manager
            mock_response = Mock()
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_response)
            mock_context.__exit__ = Mock(return_value=None)
            mock_streaming = Mock()
            mock_streaming.with_streaming_response.create.return_value = mock_context
            self.mock_client.audio.speech = mock_streaming
            
            result = helper.text_to_speech("Hello", "/tmp/test.mp3", voice='echo')
            
            self.assertTrue(result)
            mock_mkdir.assert_called_once()
    
    @patch('openai_helper.os.path.exists')
    @patch('openai_helper.os.path.isdir')
    def test_text_to_speech_failure(self, mock_isdir, mock_exists):
        """Test de text_to_speech amb fallo quan el directori no és vàlid"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock del directori existent però no és directori
            # El codi llança FileExistsError però el test ha de capturar-ho
            mock_exists.return_value = True
            mock_isdir.return_value = False
            
            # El codi llança FileExistsError dins del try, però després el captura
            # i retorna False. Però el test ha de verificar que es llança l'excepció
            # dins del try-except
            try:
                result = helper.text_to_speech("Hello", "/tmp/test.mp3", voice='echo')
                # Si arriba aquí, l'excepció ha estat capturada i retorna False
                self.assertFalse(result)
            except FileExistsError:
                # Si l'excepció no és capturada, el test falla
                self.fail("FileExistsError no hauria de ser llançada, hauria de ser capturada")
    
    @patch('openai_helper.os.path.exists')
    @patch('openai_helper.os.path.isdir')
    def test_text_to_speech_exception(self, mock_isdir, mock_exists):
        """Test de text_to_speech amb excepció"""
        with patch('openai_helper.OpenAI', return_value=self.mock_client):
            helper = OpenAiHelper(self.api_key, self.assistant_id, self.assistant_name)
            
            # Mock del directori existent
            mock_exists.return_value = True
            mock_isdir.return_value = True
            
            # Mock del streaming response que llança excepció
            mock_streaming = Mock()
            mock_streaming.with_streaming_response.create.side_effect = Exception("TTS error")
            self.mock_client.audio.speech = mock_streaming
            
            result = helper.text_to_speech("Hello", "/tmp/test.mp3", voice='echo')
            
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()

