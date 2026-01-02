"""
Tests unitaris per a openai_helper.py
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import sys
import os

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
        self.mock_client.beta.threads.runs.create_and_poll.return_value = self.mock_run
    
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
            self.mock_client.beta.threads.messages.create.assert_called_once()
            self.mock_client.beta.threads.runs.create_and_poll.assert_called_once()
    
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


if __name__ == '__main__':
    unittest.main()

