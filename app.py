import os
import streamlit as st
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import speech_recognition as sr
from gtts import gTTS
import pygame
import tempfile
import threading
from langflow.load import run_flow_from_json
from streamlit_chat import message

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

TWEAKS = {
  "ChatInput-Leoja": {},
  "Prompt-NC0yX": {},
  "OpenAIModel-pKvxn": {},
  "ChatOutput-vn6hr": {},
  "Chroma-dxJAT": {},
  "ParseData-vQg6b": {},
  "File-ZsWtg": {},
  "RecursiveCharacterTextSplitter-wPdPQ": {},
  "OpenAIEmbeddings-yMreO": {},
  "Chroma-OrTkL": {}
}

translator = GoogleTranslator(source='auto')
r = sr.Recognizer()

if "listening" not in st.session_state:
    st.session_state.listening = False
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'is_speaking' not in st.session_state:
    st.session_state.is_speaking = False
if 'last_spoken_text' not in st.session_state:
    st.session_state.last_spoken_text = None
if 'speech_complete' not in st.session_state:
    st.session_state.speech_complete = True

def SpeakText(text, lang='en'):
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_filename = temp_file.name
        temp_file.close()
        
        st.session_state.is_speaking = True
        st.session_state.speech_complete = False
        
        tts = gTTS(text=text, lang=lang)
        tts.save(temp_filename)
        
        pygame.mixer.init()
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        pygame.mixer.quit()
        os.remove(temp_filename)
        
        st.session_state.is_speaking = False
        st.session_state.speech_complete = True
        st.session_state.last_spoken_text = text
        st.rerun()
        
    except Exception as e:
        print(f"Error in text-to-speech: {str(e)}")
        st.session_state.is_speaking = False
        st.session_state.speech_complete = True
        st.rerun()

def translate_text(text, target_language):
    if target_language == "ta":
        return translator.translate(text, target='ta')
    elif target_language == "en":
        return translator.translate(text, target='en')
    return text

def start_listening(language='en'):
    st.session_state.listening = True
    st.session_state.transcription = ""
    
    status_placeholder = st.empty()
    with status_placeholder:
        st.info("Listening now...")  
    
    with sr.Microphone() as source:
        try:
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.listen(source, phrase_time_limit=5)
            text = r.recognize_google(audio, language=language)
            st.session_state.transcription = text
            st.session_state.user_input = text 
            st.session_state.listening = False
            status_placeholder.empty()
            process_input()
        except sr.UnknownValueError:
            st.session_state.listening = False
            status_placeholder.empty()
        except sr.RequestError as e:
            st.session_state.listening = False
            status_placeholder.empty()
        except Exception as e:
            st.session_state.listening = False
            status_placeholder.empty()

def process_input():
    user_input = st.session_state.user_input  
    selected_language = st.session_state.selected_language
    translated_input = translate_text(user_input, target_language="en")
    
    if translated_input:
        if translated_input.lower() in ['quit', 'exit', 'bye', 'thank you']:
            if selected_language == 'ta': 
                thank_you_msg = "இந்த போட்டைப் பயன்படுத்தியதற்கு நன்றி."
            else:
                thank_you_msg = "Thank you for using this bot. Have a great day!"
            st.session_state.user_input = ""  
            st.session_state.chat_history.append((user_input, thank_you_msg))
            st.success(thank_you_msg)
            st.session_state.disable_input = True

        elif translated_input.lower() in ['hi','hello','hey','good morning','good afternoon','good evening','hey there','hello there']:
            if selected_language == 'ta':
                bot_response = "வணக்கம்! நான் உங்களுக்கு எப்படி உதவ முடியும்?"
            else:
                bot_response = "Hello! How can I assist you today?"

        else:
            try:
                result = run_flow_from_json(flow="Osteo bot.json",
                                            input_value=user_input,
                                            fallback_to_env_vars=True,
                                            tweaks=TWEAKS)

                bot_response = result[0].outputs[0].outputs['message']['message']['text']
            except (KeyError, IndexError, TypeError) as e:
                bot_response = "Sorry, I couldn't retrieve the response."

    if selected_language == 'ta':
        translator1 = GoogleTranslator(source='en', target='ta')
        bot_response = translator1.translate(bot_response)

    st.session_state.chat_history.append((user_input, bot_response))
    st.session_state.transcription = ""
    st.session_state.user_input = ""
    st.rerun()  

def eng_out():
    st.title("Chatbot for Osteomyelitis (English)")

    chat_container = st.container()
    with chat_container:
        for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history):
            message(user_msg, is_user=True, key=f"user_msg_{i}")
            message(bot_msg, key=f"bot_msg_{i}")
            
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if st.button("🔊", key=f"speak_{i}"):
                    if not st.session_state.is_speaking:
                        threading.Thread(target=SpeakText, args=(bot_msg, 'en')).start()

    if not st.session_state.is_speaking or st.session_state.speech_complete:
        input_placeholder = "Listening..." if st.session_state.listening else "Type something..."
        user_input = st.text_input(
            input_placeholder,
            key="user_input",
            value="",
            disabled=st.session_state.listening,
            on_change=process_input
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.button(
                "🎤 Speak", 
                key="speak_button",
                on_click=start_listening,  
                disabled=st.session_state.listening,
                use_container_width=True
            )

def tam_out():
    st.title("ஆஸ்டியோமைலிடிஸிற்கான சாட்போட் (தமிழ்)")

    chat_container = st.container()
    with chat_container:
        for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history):
            message(user_msg, is_user=True, key=f"user_msg_{i}")
            message(bot_msg, key=f"bot_msg_{i}")
            
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if st.button("🔊", key=f"speak_{i}"):
                    if not st.session_state.is_speaking:
                        threading.Thread(target=SpeakText, args=(bot_msg, 'ta')).start()

    if not st.session_state.is_speaking or st.session_state.speech_complete:
        input_placeholder = "கேட்கிறது..." if st.session_state.listening else "எதையாவது எழுதுங்கள்..."
        user_input = st.text_input(
            input_placeholder,
            key="user_input",
            value="",
            disabled=st.session_state.listening,
            on_change=process_input
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.button(
                "🎤 பேசவும்", 
                key="speak_button_ta",
                on_click=lambda: start_listening(language='ta-IN'),  
                disabled=st.session_state.listening,
                use_container_width=True
            )

def main():
    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = 'en'

    language = st.radio("Choose Language", ('English', 'Tamil'))

    if language == 'English':
        st.session_state.selected_language = 'en'
        eng_out()
    else:
        st.session_state.selected_language = 'ta'
        tam_out()

if __name__ == "__main__":
    main()