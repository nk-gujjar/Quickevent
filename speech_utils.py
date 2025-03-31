import streamlit as st
import speech_recognition as sr
import tempfile
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def record_and_transcribe():
    """
    Record audio using Streamlit's file uploader and transcribe it to text
    using the SpeechRecognition library.
    
    Returns:
        str: Transcribed text or error message
    """
    st.write("📢 Record your event details")
    
    # Create a file uploader for audio
    audio_file = st.file_uploader("Upload audio file", type=["wav", "mp3", "m4a"])
    
    # Button to start recording
    record_button = st.button("🎙️ Record Audio")
    
    if record_button:
        # Display recording controls
        with st.spinner("Recording... Press 'Stop' when finished"):
            # Create a recognizer instance
            recognizer = sr.Recognizer()
            
            # Use the microphone as source
            try:
                with sr.Microphone() as source:
                    st.info("Recording started. Speak now...")
                    # Adjust for ambient noise
                    recognizer.adjust_for_ambient_noise(source)
                    # Record audio
                    audio_data = recognizer.listen(source, timeout=10)
                    st.success("Recording complete!")
                    
                    # Save the audio file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                        temp_audio.write(audio_data.get_wav_data())
                        temp_audio_path = temp_audio.name
                    
                    # Transcribe the audio
                    try:
                        transcribed_text = recognizer.recognize_google(audio_data)
                        st.success("Transcription complete!")
                        return transcribed_text
                    except sr.UnknownValueError:
                        st.error("Could not understand the audio")
                        return None
                    except sr.RequestError as e:
                        st.error(f"Could not request results from Google Speech Recognition service; {e}")
                        return None
                    finally:
                        # Clean up the temporary file
                        if os.path.exists(temp_audio_path):
                            os.unlink(temp_audio_path)
            except Exception as e:
                st.error(f"Error recording audio: {str(e)}")
                logger.error(f"Error recording audio: {str(e)}")
                return None
    
    # Process uploaded audio file
    if audio_file is not None:
        st.audio(audio_file, format="audio/wav")
        
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(audio_file.read())
            temp_audio_path = temp_audio.name
        
        try:
            # Create a recognizer instance
            recognizer = sr.Recognizer()
            
            # Load the audio file
            with sr.AudioFile(temp_audio_path) as source:
                # Read the audio data
                audio_data = recognizer.record(source)
                
                # Transcribe the audio
                try:
                    transcribed_text = recognizer.recognize_google(audio_data)
                    st.success("Transcription complete!")
                    return transcribed_text
                except sr.UnknownValueError:
                    st.error("Could not understand the audio")
                    return None
                except sr.RequestError as e:
                    st.error(f"Could not request results from Google Speech Recognition service; {e}")
                    return None
        except Exception as e:
            st.error(f"Error processing audio file: {str(e)}")
            logger.error(f"Error processing audio file: {str(e)}")
            return None
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
    
    return None