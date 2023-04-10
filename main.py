import asyncio
import re
import openai
import whisper
import boto3
import pydub
from pydub import playback
import speech_recognition as sr
from EdgeGPT import Chatbot, ConversationStyle

openai.api_key = ""

recognizer = sr.Recognizer()
BING_WAKEUP = "bing"
GPT_WAKEUP = "gpt"

# function to get the wake word
def getWakeWord(input):
    if BING_WAKEUP in input.lower():
        return BING_WAKEUP
    elif GPT_WAKEUP in input.lower():
        return GPT_WAKEUP
    else:
        return None

def synthesizeSpeech(text, outputFile):
    polly = boto3.client('polly', region_name='us-east-1')
    response = polly.synthesize_speech(
        Text = text,
        OutputFormat = 'mp3',
        VoiceId = 'Joanna',
        Engine = 'neural'
    )

    with open(outputFile, 'wb') as f:
        f.write(response['AudioStream'].read())

def playAudio(file):
    sound = pydub.AudioSegment.from_file(file, format="mp3")
    playback.play(sound)

async def main():
    # loops until stopped
    while True:
        # setting up the microphone and transcribing the audio in order to be sent to gpt
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print(f"Waiting for wakeup word 'bing' or 'gpt'")
            while True:
                audio = recognizer.listen(source)
                try:
                    with open("audio.mp3", "wb") as f:
                        f.write(audio.get_wav_data())
                    model = whisper.load_model("tiny")
                    result = model.transcribe("audio.mp3")
                    phrase = result["text"]
                    print(f"You said: {phrase}")

                    wakeup = getWakeWord(phrase)
                    if wakeup is not None:
                        break
                    else:
                        print("Not a wakeup word.")
                except Exception as e:
                    print("Error in audio transcription: {0}".format(e))
                    continue
        
            print("Speak a prompt...")
            synthesizeSpeech('What can I help you with?', 'response.mp3')
            playAudio('response.mp3')
            audio = recognizer.listen(source)

            try:
                with open("audio_prompt.mp3", "wb") as f:
                    f.write(audio.get_wav_data())
                model = whisper.load_model("base")
                result = model.transcribe("audio_prompt.mp3")
                user_input = result["text"]
                print(f"You said: {user_input}")
            except Exception as e:
                print("Error in audio transcription: {0}".format(e))
                continue

            if wakeup == BING_WAKEUP:
                # starting up the bing ai bot using the cookies for the newest edge (required to use Bing AI)
                bingBot = Chatbot(cookiePath='cookies.json')

                # Asking a question and awaiting the response
                response = await bingBot.ask(prompt=user_input, conversation_style = ConversationStyle.creative)

                # Filtering the message to just display a response and not the whole json
                for message in response["item"]["messages"]:
                    if message["author"] == "bot":
                        botResponse = message["text"]

                # Filtering out links using a regex
                botResponse = re.sub('\[\^\d+\^\]', '', botResponse)
            else:
                # Send prompt to GPT-3.5-turbo API
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content":
                        "You are a helpful assistant."},
                        {"role": "user", "content": user_input},
                    ],
                    temperature=0.5,
                    max_tokens=150,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    n=1,
                    stop=["\nUser:"],
                )

                bot_response = response["choices"][0]["message"]["content"]

        # Printing the Response
        print("Bot Response: ", botResponse)
        synthesizeSpeech(botResponse, 'response.mp3')
        playAudio('response.mp3')

        #closing the bot
        await bingBot.close()


if __name__ == "__main__":
    asyncio.run(main())