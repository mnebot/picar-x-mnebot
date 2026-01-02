from openai import OpenAI
import time
import shutil
import os
import json

# utils
# =================================================================
def chat_print(label, message):
    # --- normal print ---
    print(f'{time.time():.3f} {label:>6} >>> {message}')

# OpenAiHelper
# =================================================================
class OpenAiHelper():
    STT_OUT = "stt_output.wav"
    TTS_OUTPUT_FILE = 'tts_output.mp3'
    TIMEOUT = 30 # seconds

    def __init__(self, api_key, assistant_id, assistant_name, timeout=TIMEOUT) -> None:
        
        self.api_key = api_key
        self.assistant_id = assistant_id
        self.assistant_name = assistant_name

        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.thread = self.client.beta.threads.create()
        self.run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=assistant_id,
        )

    def stt(self, audio, language='en'):
        try:
            import wave
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

        # recognize speech using Whisper API
        try:
            return recognizer.recognize_whisper_api(audio, api_key=self.api_key)
        except sr.RequestError as e:
            print(f"Could not request results from Whisper API; {e}")
            return False

    def _prepare_message_with_language(self, msg):
        """Prepara el missatge afegint la instrucció de llengua."""
        return f"Respon sempre en català. {msg}"

    def _parse_response_value(self, value):
        """Intenta parsejar el valor com JSON, retorna string si falla."""
        try:
            return json.loads(value)  # Convertir JSON string a dict de forma segura
        except (TypeError, ValueError):
            return str(value)

    def _extract_assistant_response(self, messages):
        """Extreu la resposta de l'assistent dels missatges."""
        for message in messages.data:
            if message.role == 'assistant':
                for block in message.content:
                    if block.type == 'text':
                        value = block.text.value
                        chat_print(self.assistant_name, value)
                        return self._parse_response_value(value)
            break  # only last reply
        return None

    def _process_run_response(self, run):
        """Processa el run i retorna la resposta de l'assistent o None."""
        if run.status == 'completed': 
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread.id
            )
            return self._extract_assistant_response(messages)
        else:
            print(f"Run status: {run.status}")
            return None

    def dialogue(self, msg):
        chat_print("user", msg)
        msg_with_lang = self._prepare_message_with_language(msg)
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=msg_with_lang
        )
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant_id,
        )
        return self._process_run_response(run)


    def dialogue_with_img(self, msg, img_path):
        chat_print(f"user", msg)

        # Utilitzar context manager per assegurar que el fitxer es tanqui correctament
        with open(img_path, "rb") as img_file_handle:
            img_file = self.client.files.create(
                        file=img_file_handle,
                        purpose="vision"
                    )

        msg_with_lang = self._prepare_message_with_language(msg)

        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=[
                {
                    "type": "text",
                    "text": msg_with_lang
                },
                {
                    "type": "image_file",
                    "image_file": {"file_id": img_file.id}
                }
            ],
        )
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant_id,
        )
        return self._process_run_response(run)


    def text_to_speech(self, text, output_file, voice='alloy', response_format="mp3", speed=1, instructions=''):
        '''
        voice: alloy, echo, fable, onyx, nova, and shimmer
        '''
        try:
            # check dir
            dir = os.path.dirname(output_file)
            if not os.path.exists(dir):
                os.mkdir(dir)
            elif not os.path.isdir(dir):
                raise FileExistsError(f"\'{dir}\' is not a directory")

            # tts
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

