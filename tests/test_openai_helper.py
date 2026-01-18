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
    pass


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


if __name__ == '__main__':
    unittest.main()
