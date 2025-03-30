import os
import requests
import base64
import json
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from google.cloud import texttospeech, speech
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load Google Credentials from environment variable
google_creds = json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
credentials = service_account.Credentials.from_service_account_info(google_creds)

# Initialize Google Cloud clients with credentials
tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
speech_client = speech.SpeechClient(credentials=credentials)

# Twilio Credentials
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

app = Flask(__name__)

# Function: Convert text to speech using Google Cloud
def text_to_speech_google(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)
    response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    return response.audio_content

# Function: Convert speech to text using Google Cloud
def speech_to_text_google(audio_content):
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, sample_rate_hertz=8000, language_code="en-US")
    response = speech_client.recognize(config=config, audio=audio)
    if response.results:
        return response.results[0].alternatives[0].transcript
    return None

# Twilio Voice API Endpoint
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    gather = Gather(input='speech', timeout=5, action='/process_speech')
    gather.say("Hello! How can I assist you today?")
    response.append(gather)
    response.say("Sorry, I didn't get that. Goodbye.")
    return str(response)

# Process User Speech
@app.route("/process_speech", methods=['GET', 'POST'])
def process_speech():
    response = VoiceResponse()
    recording_url = request.form.get('RecordingUrl')

    if recording_url:
        try:
            # Download the audio file from Twilio
            audio_data = requests.get(recording_url).content
            user_text = speech_to_text_google(audio_data)

            if user_text:
                bot_response = f"You said: {user_text}. I'm here to help!"
                tts_audio = text_to_speech_google(bot_response)
                encoded_audio = base64.b64encode(tts_audio).decode('utf-8')
                response.say(f'<audio src="data:audio/l16;base64,{encoded_audio}"/>')
            else:
                response.say("Sorry, I didn't understand that.")
        except Exception as e:
            print(f"Error: {e}")
            response.say("An error occurred. Please try again.")
    
    gather = Gather(input='speech', timeout=5, action='/process_speech')
    response.append(gather)
    return str(response)

# Run the Flask app
if __name__ == "__main__":
    app.run()
