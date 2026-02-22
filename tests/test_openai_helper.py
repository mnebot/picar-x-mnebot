"""
Tests unitaris per a openai_helper.py (Responses API)
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Mock de les dependències externes abans d'importar el mòdul
mock_openai = MagicMock()
sys.modules['openai'] = mock_openai

# Afegir el directori pare al path per poder importar els mòduls
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carregar el mòdul real (altres tests el reemplacen per un mock)
if 'openai_helper' in sys.modules:
    del sys.modules['openai_helper']

from openai_helper import OpenAiHelper, chat_print


class TestChatPrint(unittest.TestCase):
    """Tests per a la funció chat_print"""

    @patch('builtins.print')
    def test_chat_print_formats_message(self, mock_print):
        """Test que chat_print imprimeix amb format label i missatge"""
        chat_print("user", "Hola robot")
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        self.assertIn("user", call_args)
        self.assertIn("Hola robot", call_args)


class TestOpenAiHelperInit(unittest.TestCase):
    """Tests per al constructor OpenAiHelper amb Responses API"""

    @patch('openai_helper.OpenAI')
    def test_init_with_model(self, mock_openai_class):
        """model_or_prompt_id com a model estableix self.model"""
        h = OpenAiHelper(api_key="key", model_or_prompt_id="gpt-4.1-mini")
        self.assertIsNone(h.prompt_id)
        self.assertEqual(h.model, "gpt-4.1-mini")

    @patch('openai_helper.OpenAI')
    def test_init_with_prompt_id(self, mock_openai_class):
        """model_or_prompt_id començant per prompt_ estableix self.prompt_id"""
        h = OpenAiHelper(api_key="key", model_or_prompt_id="prompt_abc123")
        self.assertEqual(h.prompt_id, "prompt_abc123")
        self.assertIsNone(h.model)

    @patch('openai_helper.OpenAI')
    def test_init_with_asst_passes_through_as_model(self, mock_openai_class):
        """asst_xxx es passa tal qual com a model (el handling legacy es fa upstream a keys/gpt_car)"""
        h = OpenAiHelper(api_key="key", model_or_prompt_id="asst_xxx")
        self.assertIsNone(h.prompt_id)
        self.assertEqual(h.model, "asst_xxx")

    @patch('openai_helper.OpenAI')
    def test_init_none_uses_default_model(self, mock_openai_class):
        """model_or_prompt_id None usa DEFAULT_MODEL"""
        h = OpenAiHelper(api_key="key")
        self.assertEqual(h.model, OpenAiHelper.DEFAULT_MODEL)

    @patch('openai_helper.OpenAI')
    def test_init_with_instructions_path(self, mock_openai_class):
        """instructions_path vàlid carrega les instruccions"""
        with patch('builtins.open', unittest.mock.mock_open(read_data='Instruccions de prova')):
            with patch('os.path.isfile', return_value=True):
                h = OpenAiHelper(api_key="key", instructions_path="/path/instruccions.txt")
        self.assertEqual(h._instructions, 'Instruccions de prova')

    @patch('openai_helper.OpenAI')
    def test_init_instructions_path_missing_keeps_none(self, mock_openai_class):
        """instructions_path inexistent manté _instructions a None"""
        with patch('os.path.isfile', return_value=False):
            h = OpenAiHelper(api_key="key", instructions_path="/noexisteix.txt")
        self.assertIsNone(h._instructions)


class TestOpenAiHelperParseResponse(unittest.TestCase):
    """Tests per a _parse_response_value"""

    @patch('openai_helper.OpenAI')
    def test_parse_response_value_json_dict(self, mock_openai_class):
        """JSON vàlid es converteix a dict"""
        h = OpenAiHelper(api_key="key")
        data = {"actions": [], "answer": "Hola"}
        result = h._parse_response_value(json.dumps(data))
        self.assertEqual(result, data)

    @patch('openai_helper.OpenAI')
    def test_parse_response_value_invalid_json_returns_str(self, mock_openai_class):
        """JSON invàlid retorna str del valor"""
        h = OpenAiHelper(api_key="key")
        result = h._parse_response_value("text pla")
        self.assertEqual(result, "text pla")

    @patch('openai_helper.OpenAI')
    def test_parse_response_value_none_returns_str_none(self, mock_openai_class):
        """None retorna 'None' com a str"""
        h = OpenAiHelper(api_key="key")
        result = h._parse_response_value(None)
        self.assertEqual(result, "None")


class TestOpenAiHelperPrepareMessage(unittest.TestCase):
    """Tests per a _prepare_message_with_language"""

    @patch('openai_helper.OpenAI')
    def test_prepare_message_adds_catalan_prefix(self, mock_openai_class):
        """Afegix el prefix 'Respon sempre en català.'"""
        h = OpenAiHelper(api_key="key")
        msg = h._prepare_message_with_language("Com et dius?")
        self.assertTrue(msg.startswith("Respon sempre en català."))
        self.assertIn("Com et dius?", msg)


class TestOpenAiHelperCallResponsesApi(unittest.TestCase):
    """Tests per a _call_responses_api"""

    @patch('openai_helper.OpenAI')
    def test_call_responses_api_completed_returns_parsed(self, mock_openai_class):
        """Resposta completed retorna el valor parsejat"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_resp = Mock()
        mock_resp.status = "completed"
        mock_resp.output_text = '{"answer": "Hola", "actions": []}'
        mock_resp.id = "resp_123"
        mock_client.responses.create.return_value = mock_resp

        h = OpenAiHelper(api_key="key")
        result = h._call_responses_api("Hola")
        self.assertEqual(result, {"answer": "Hola", "actions": []})
        self.assertEqual(h._last_response_id, "resp_123")

    @patch('openai_helper.OpenAI')
    def test_call_responses_api_failed_returns_none(self, mock_openai_class):
        """Resposta status != completed retorna None"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_resp = Mock()
        mock_resp.status = "failed"
        mock_resp.last_error = None
        mock_client.responses.create.return_value = mock_resp

        h = OpenAiHelper(api_key="key")
        with patch('openai_helper.print'):
            result = h._call_responses_api("Hola")
        self.assertIsNone(result)

    @patch('openai_helper.OpenAI')
    def test_call_responses_api_failed_logs_last_error(self, mock_openai_class):
        """Quan status failed i last_error existeix, es loga"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_err = Mock()
        mock_err.code = "server_error"
        mock_err.message = "Something went wrong"
        mock_resp = Mock()
        mock_resp.status = "failed"
        mock_resp.last_error = mock_err
        mock_client.responses.create.return_value = mock_resp

        h = OpenAiHelper(api_key="key")
        with patch('openai_helper.print') as mock_print:
            h._call_responses_api("Hola")
        # Hauria d'haver cridat print per status i last_error
        self.assertGreaterEqual(mock_print.call_count, 2)

    @patch('openai_helper.OpenAI')
    def test_call_responses_api_exception_returns_none(self, mock_openai_class):
        """Excepció en responses.create retorna None"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.responses.create.side_effect = Exception("API error")

        h = OpenAiHelper(api_key="key")
        with patch('openai_helper.print'):
            result = h._call_responses_api("Hola")
        self.assertIsNone(result)

    @patch('openai_helper.OpenAI')
    def test_call_responses_api_uses_prompt_id_when_set(self, mock_openai_class):
        """Quan prompt_id està definit, es passa a l'API"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_resp = Mock()
        mock_resp.status = "completed"
        mock_resp.output_text = '{"answer": "ok"}'
        mock_resp.id = "r1"
        mock_client.responses.create.return_value = mock_resp

        h = OpenAiHelper(api_key="key", model_or_prompt_id="prompt_xyz")
        h._call_responses_api("Test")
        call_kwargs = mock_client.responses.create.call_args[1]
        self.assertIn("prompt", call_kwargs)
        self.assertEqual(call_kwargs["prompt"]["prompt_id"], "prompt_xyz")

    @patch('openai_helper.OpenAI')
    def test_call_responses_api_uses_previous_response_id(self, mock_openai_class):
        """Quan _last_response_id existeix, es passa previous_response_id"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_resp = Mock()
        mock_resp.status = "completed"
        mock_resp.output_text = '{"answer": "ok"}'
        mock_resp.id = "r2"
        mock_client.responses.create.return_value = mock_resp

        h = OpenAiHelper(api_key="key")
        h._last_response_id = "resp_prev"
        h._call_responses_api("Següent missatge")
        call_kwargs = mock_client.responses.create.call_args[1]
        self.assertEqual(call_kwargs.get("previous_response_id"), "resp_prev")


class TestOpenAiHelperDialogue(unittest.TestCase):
    """Tests per a dialogue i dialogue_with_img"""

    @patch('openai_helper.OpenAI')
    def test_dialogue_calls_call_responses_api(self, mock_openai_class):
        """dialogue crida _call_responses_api amb missatge preparat"""
        h = OpenAiHelper(api_key="key")
        h._call_responses_api = Mock(return_value={"answer": "Resposta"})
        with patch('openai_helper.chat_print'):
            result = h.dialogue("Hola")
        h._call_responses_api.assert_called_once()
        arg = h._call_responses_api.call_args[0][0]
        self.assertIn("Respon sempre en català", arg)
        self.assertIn("Hola", arg)
        self.assertEqual(result, {"answer": "Resposta"})

    @patch('openai_helper.OpenAI')
    def test_dialogue_with_img_creates_file_and_calls_api(self, mock_openai_class):
        """dialogue_with_img crea fitxer, l'adjunta i crida _call_responses_api"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_file = Mock()
        mock_file.id = "file_abc"
        mock_client.files.create.return_value = mock_file
        mock_resp = Mock()
        mock_resp.status = "completed"
        mock_resp.output_text = '{"answer": "ok", "actions": []}'
        mock_resp.id = "r1"
        mock_client.responses.create.return_value = mock_resp

        h = OpenAiHelper(api_key="key")
        with patch('builtins.open', unittest.mock.mock_open(read_data=b'fake_img')):
            with patch('openai_helper.chat_print'):
                result = h.dialogue_with_img("Què veus?", "/tmp/img.jpg")
        mock_client.files.create.assert_called_once()
        call_input = mock_client.responses.create.call_args[1]["input"]
        self.assertIsInstance(call_input, list)
        self.assertEqual(len(call_input), 1)
        content = call_input[0]["content"]
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]["type"], "input_text")
        self.assertEqual(content[1]["type"], "input_image")
        self.assertEqual(content[1]["file_id"], "file_abc")
        self.assertEqual(result, {"answer": "ok", "actions": []})


class TestOpenAiHelperTTS(unittest.TestCase):
    """Tests per a text_to_speech"""

    @patch('openai_helper.OpenAI')
    def test_text_to_speech_creates_dir_and_streams(self, mock_openai_class):
        """text_to_speech crea directori si no existeix i crida stream_to_file"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_stream = MagicMock()
        mock_stream.stream_to_file = Mock()
        mock_cm = MagicMock()
        mock_cm.__enter__ = Mock(return_value=mock_stream)
        mock_cm.__exit__ = Mock(return_value=False)
        mock_client.audio.speech.with_streaming_response.create.return_value = mock_cm

        h = OpenAiHelper(api_key="key")
        with patch('os.path.exists', return_value=False):
            with patch('os.makedirs'):
                with patch('os.path.isdir', return_value=True):
                    result = h.text_to_speech("Hola", "/out/tts/speech.mp3")
        self.assertTrue(result)
        mock_stream.stream_to_file.assert_called_once_with("/out/tts/speech.mp3")

    @patch('openai_helper.OpenAI')
    def test_text_to_speech_exception_returns_false(self, mock_openai_class):
        """Excepció en TTS retorna False"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.audio.speech.with_streaming_response.create.side_effect = Exception("TTS err")

        h = OpenAiHelper(api_key="key")
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=True):
                with patch('openai_helper.print'):
                    result = h.text_to_speech("Hola", "/out/speech.mp3")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
