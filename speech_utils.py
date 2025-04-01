import streamlit as st
import tempfile
import os
import logging
import base64
import sounddevice as sd
import numpy as np
import wave
import threading
import queue
from dotenv import load_dotenv
from groq import Groq  

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Ensure API key is set
if not GROQ_API_KEY:
    st.error("GROQ API key not found. Please set GROQ_API_KEY in .env file.")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Global variables for recording
audio_queue = queue.Queue()
is_recording = False
recording_thread = None
recorded_file_path = None  # Store the recorded file path


def audio_callback(indata, frames, time, status):
    """Callback function for recording audio"""
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(indata.copy())


def start_recording():
    """Start recording audio in a separate thread"""
    global is_recording, recording_thread, audio_queue, recorded_file_path

    # Clear the queue
    while not audio_queue.empty():
        audio_queue.get()

    is_recording = True

    def record_audio():
        """Record audio and save to a temporary file"""
        print("Recording started...")
        sample_rate = 16000
        channels = 1

        try:
            with sd.InputStream(samplerate=sample_rate, channels=channels, callback=audio_callback):
                # Create temporary file for saving the audio
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_filepath = temp_file.name
                temp_file.close()

                # Setup the WAV file
                with wave.open(temp_filepath, 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(2)  # 16-bit audio
                    wf.setframerate(sample_rate)

                    print(f"Saving audio to {temp_filepath}")

                    # Record until stopped
                    while is_recording:
                        try:
                            data = audio_queue.get(timeout=0.1)
                            wf.writeframes((data * 32767).astype(np.int16).tobytes())
                        except queue.Empty:
                            continue

                # Save the file path for later access
                global recorded_file_path
                recorded_file_path = temp_filepath

        except Exception as e:
            logger.error(f"Error recording audio: {str(e)}")
            print(f"Error recording audio: {str(e)}")
            recorded_file_path = None

    # Start recording in a separate thread
    recording_thread = threading.Thread(target=record_audio)
    recording_thread.start()


def stop_recording():
    """Stop the recording and return the path to the recorded file"""
    global is_recording, recording_thread, recorded_file_path

    if not is_recording:
        return None

    is_recording = False

    # Wait for recording thread to finish
    if recording_thread:
        print("Stopping recording...")
        recording_thread.join()
        temp_filepath = recorded_file_path
        recording_thread = None  # Reset thread variable

        return temp_filepath

    return None


def transcribe_with_groq(audio_file_path):
    """
    Transcribe audio using Groq's Whisper API
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY_Whisper not found in environment variables")

    try:
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_file_path, file.read()),
                model="whisper-large-v3",
                response_format="verbose_json"
            )

            print(f"Transcription received: {transcription.text}")
            return transcription.text
    except Exception as e:
        logger.error(f"Error with Groq API: {str(e)}")
        st.error(f"Error transcribing audio: {str(e)}")
        return None



def add_mic_to_chat_input():
    """Add a microphone button to handle voice input."""
    if 'recording' not in st.session_state:
        st.session_state.recording = False
        st.session_state.transcribed_text = None

    # Display appropriate button based on the recording state
    if not st.session_state.recording:
        if st.button("🎙️ Start Recording"):
            st.session_state.recording = True
            start_recording()
            st.rerun()
    else:
        if st.button("⏹️ Stop Recording"):
            st.session_state.recording = False
            temp_filepath = stop_recording()
            if temp_filepath and os.path.exists(temp_filepath):
                with st.spinner("Transcribing..."):
                    transcribed_text = transcribe_with_groq(temp_filepath)

                if transcribed_text:
                    st.session_state.transcribed_text = transcribed_text
                else:
                    st.error("Failed to transcribe audio.")

                os.unlink(temp_filepath)  # Clean up file
            st.rerun()

    # Display transcribed text if available
    return st.session_state.get('transcribed_text')



# Example usage in a Streamlit app
if __name__ == '__main__':
    st.title("🎤 AI Voice Transcription")
    transcribed_text = add_mic_to_chat_input()
    if transcribed_text:
        st.write("📝 Transcribed Text:", transcribed_text)
