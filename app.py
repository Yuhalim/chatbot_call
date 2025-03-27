from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from google.cloud import texttospeech, speech
import os
import requests
import base64

app = Flask(__name__)

# Google Cloud setup
tts_client = texttospeech.TextToSpeechClient()
speech_client = speech.SpeechClient()
project_id = os.environ.get('prime-cosmos-418312')
language_code = "en-US"

def text_to_speech_google(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)
    response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    return response.audio_content

def speech_to_text_google(audio_content):
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, sample_rate_hertz=8000, language_code=language_code)
    response = speech_client.recognize(config=config, audio=audio)
    if response.results:
        return response.results[0].alternatives[0].transcript
    else:
        return None

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    gather = Gather(input='speech', timeout=5, action='/process_speech')
    gather.say("Hello! How can I help you?")
    response.append(gather)
    response.say("Sorry, I didn't get that. Goodbye.")
    return str(response)

@app.route("/process_speech", methods=['GET', 'POST'])
def process_speech():
    response = VoiceResponse()
    recording_url = request.form.get('RecordingUrl')

    if recording_url:
        try:
            audio_data = requests.get(recording_url).content
            user_text = speech_to_text_google(audio_data)

            if user_text:
                bot_response = f"You said: {user_text}"
                tts_audio = text_to_speech_google(bot_response)
                encoded_audio = base64.b64encode(tts_audio).decode('utf-8')
                response.say(f'<audio src="data:audio/l16;base64,{encoded_audio}"/>')
                gather = Gather(input='speech', timeout=5, action='/process_speech')
                response.append(gather)
            else:
                response.say("Sorry, I didn't understand that.")
                gather = Gather(input='speech', timeout=5, action='/process_speech')
                response.append(gather)
        except Exception as e:
            print(f"Error: {e}")
            response.say("An error occurred. Please try again later.")
            gather = Gather(input='speech', timeout=5, action='/process_speech')
            response.append(gather)
    else:
        response.say("Sorry, I didn't get any input.")
        gather = Gather(input='speech', timeout=5, action='/process_speech')
        response.append(gather)
    return str(response)

if __name__ == "__main__":
    app.run(debug=True) #remove debug=True for production
