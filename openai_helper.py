"""
OpenAI API helper - Responses API (replaces deprecated Assistants API).
"""
from openai import OpenAI
import time
import os
import json

# utils
# =================================================================
def chat_print(label, message):
    print(f'{time.time():.3f} {label:>6} >>> {message}')

# OpenAiHelper - Responses API
# =================================================================
class OpenAiHelper():
    STT_OUT = "stt_output.wav"
    TTS_OUTPUT_FILE = 'tts_output.mp3'
    TIMEOUT = 30  # seconds

    def __init__(self, api_key, timeout=TIMEOUT):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self._last_response_id = None

    def stt(self, audio, language='en'):
        try:
            from io import BytesIO
            wav_data = BytesIO(audio.get_wav_data())
            wav_data.name = self.STT_OUT
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_data,
                language=language,
                prompt="aquesta és una conversa entre jo i un robot"
            )
            return transcript.text
        except Exception as e:
            print(f"stt err:{e}")
            return False

    def speech_recognition_stt(self, recognizer, audio):
        import speech_recognition as sr
        try:
            return recognizer.recognize_whisper_api(audio, api_key=self.api_key)
        except sr.RequestError as e:
            print(f"Could not request results from Whisper API; {e}")
            return False

    def _prepare_message_with_language(self, msg):
        return f"Respon sempre en català. {msg}"

    def _parse_response_value(self, value):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return str(value)

    def _call_responses_api(self, input_items):
        """Crida la Responses API i retorna la resposta parsejada o None."""
        kwargs = {
            "input": input_items,
            "store": True,
        }
        if self._last_response_id:
            kwargs["previous_response_id"] = self._last_response_id

        try:
            response = self.client.responses.create(**kwargs)
        except Exception as e:
            print(f"Responses API err: {e}")
            return None

        if response.status != "completed":
            print(f"Response status: {response.status}")
            if hasattr(response, 'last_error') and response.last_error is not None:
                err = response.last_error
                code = getattr(err, 'code', '?')
                msg = getattr(err, 'message', str(err))
                print(f"Response last_error: code={code}, message={msg}")
            return None

        self._last_response_id = response.id
        text = getattr(response, 'output_text', None) or ""
        if text:
            chat_print("response", text)
            return self._parse_response_value(text)
        return None

    def dialogue(self, msg):
        chat_print("user", msg)
        msg_with_lang = self._prepare_message_with_language(msg)
        return self._call_responses_api(msg_with_lang)

    def dialogue_with_img(self, msg, img_path):
        chat_print("user", msg)
        with open(img_path, "rb") as f:
            img_file = self.client.files.create(file=f, purpose="vision")
        msg_with_lang = self._prepare_message_with_language(msg)
        input_items = [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": msg_with_lang},
                    {"type": "input_image", "file_id": img_file.id},
                ],
            }
        ]
        return self._call_responses_api(input_items)

    def text_to_speech(self, text, output_file, voice='alloy', response_format="mp3", speed=1, instructions=''):
        try:
            dir_path = os.path.dirname(output_file)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, mode=0o755, exist_ok=True)
            elif not os.path.isdir(dir_path):
                raise FileExistsError(f"'{dir_path}' is not a directory")

            with self.client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text,
                response_format=response_format,
                speed=speed,
                instructions=instructions,
            ) as response:
                response.stream_to_file(output_file)
            return True
        except Exception as e:
            print(f'tts err: {e}')
            return False
