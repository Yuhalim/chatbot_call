# from flask import Flask, request
# from twilio.twiml.voice_response import VoiceResponse, Gather
# from twilio.rest import Client
# import os

# app = Flask(__name__)

# # Twilio Account SID and Auth Token
# account_sid = os.environ.get('US63fe38ff944c9d34f97a5ac8b4c5cb51') #replace with your SID
# auth_token = os.environ.get('5f62a6361c59be40f9ff7e652cc22dc9') #replace with your Auth Token

# client = Client(account_sid, auth_token)

# @app.route("/voice", methods=['GET', 'POST'])
# def voice():
#     """Handles incoming phone calls."""

#     response = VoiceResponse()
#     gather = Gather(input='speech', timeout=5, action='/process_speech') #timeout of 5 seconds

#     gather.say("Hello! Welcome to the chatbot. Please tell me how I can help you.")
#     response.append(gather)

#     #If user doesn't say anything, or timeout occurs.
#     response.say("Sorry, I didn't get that. Goodbye.")
#     return str(response)

# @app.route("/process_speech", methods=['GET', 'POST'])
# def process_speech():
#     """Processes the speech input from the user."""

#     response = VoiceResponse()

#     user_speech = request.form.get('SpeechResult')
#     if user_speech:
#         # Here, you'd typically send 'user_speech' to your NLP engine (e.g., Dialogflow, Lex)
#         # and receive a response. For simplicity, we'll just echo the input.
#         bot_response = f"You said: {user_speech}" #replace with your NLP response

#         response.say(bot_response)
#         response.say("Do you have any other questions?")
#         gather = Gather(input='speech', timeout=5, action='/process_speech')
#         response.append(gather) # loop the conversation.

#     else:
#         response.say("Sorry, I didn't get that. Goodbye.")

#     return str(response)

# if __name__ == "__main__":
#     app.run(debug=True) #remove debug=True for production

from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from google.cloud import texttospeech, speech
import os
import requests
import base64
import os
print(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
app = Flask(__name__)

# Google Cloud setup
tts_client = texttospeech.TextToSpeechClient()
speech_client = speech.SpeechClient()
project_id = os.environ.get('chatbot-454814')
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
