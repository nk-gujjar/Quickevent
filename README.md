
# QuickEvent - Chatbot Event Scheduler

## Description
QuickEvent is a chatbot application that allows users to schedule events in Google Calendar. It uses **Streamlit** for the frontend interface and integrates with **Groq API** for both chat and voice inputs. The chatbot processes user inputs and schedules events in Google Calendar. This project also uses **Groq API** for speech-to-text transcription and text-based interaction.

## Demo Video


https://github.com/user-attachments/assets/ddecc8d1-d226-4f2b-9a65-8b54a8e9e21c




## Features
- **User-friendly interface** powered by **Streamlit**.
- Seamless interaction with the chatbot using the **Groq API** for both voice and text inputs.
- Integration with **Google Calendar** for event scheduling.
- **Voice-to-Text** transcription through the **Groq API**.
- Confirmation flow for event scheduling.
- Customizable and scalable for various event types and use cases.

## Requirements
Ensure you have the following dependencies installed:

- Python 3.x
- **Streamlit**: Frontend framework.
- **Groq API**: Required for chat and speech-to-text transcription.
- **Google Calendar API credentials**: Required for Google Calendar integration.

## Installation

1. **Clone this repository** to your local machine:

   ```bash
   https://github.com/nk-gujjar/Quickevent.git
   cd Quickevent
   ```

2. **Install the required dependencies** using pip:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Calendar API credentials**:
   - Go to the [Google Developer Console](https://console.developers.google.com/).
   - Create a new project.
   - Enable the **Google Calendar API**.
   - Create **OAuth 2.0 credentials** and download the `credentials.json` file.
   - Place this file in your project directory.

4. **Set up Groq API for chat and voice transcription**:
   - Sign up for **Groq API** access: [Groq API](https://www.groq.com/).
   - Obtain your **API key**.
   - Make sure the Groq API endpoint is correctly integrated into your project.

5. **Run the application**:

   To start the Streamlit application, run:

   ```bash
   streamlit run app.py
   ```

6. **Access the application**:
   Open your browser and navigate to the address shown in the terminal (usually `http://localhost:8501`).

## Features & How it Works

### 1. **Chat Input**
   - The user can interact with the chatbot via **text input**. The chatbot uses **Groq API** to process the text input and extract event details such as:
     - Event title
     - Event description
     - Start time
     - End time
     - Attendees

### 2. **Voice Input**
   - The user can also speak to the chatbot. The **Groq API** is used to transcribe the **audio input** into **text**. Once transcribed, the Groq model processes the text and extracts event details to schedule the event.

### 3. **Event Scheduling**
   After extracting the event details from the user input (either chat or voice), the chatbot confirms the event details with the user before scheduling it.

   **Confirmation flow:**
   - The chatbot displays the event details to the user.
   - The user is prompted with a **"Yes"** or **"No"** button to confirm or reject the event details.
   - If the user clicks **"Yes"**, the event is added to the Google Calendar.
   - If the user clicks **"No"**, the event scheduling is canceled.

### 4. **Google Calendar Integration**
   - The event details extracted by **Groq API** are used to create an event in the user’s **Google Calendar**.
   - The event includes the following:
     - Title
     - Location
     - Description
     - Start time
     - End time
     - Attendees

### 5. **Error Handling**
   - If the chatbot is unable to extract date and time details from the input, it will prompt the user for more specific information.

## API Usage

### 1. **Groq API for Chat and Transcription**:
   - The **Groq API** is used to convert both voice input into text and process the text chat input.
   - The transcription is done using the **Whisper-large-v3 model** via the Groq API.
   - The Groq API processes both **text** and **speech** to extract event details.

### 2. **Google Calendar API for Event Scheduling**:
   - The event details extracted by **Groq API** are used to create an event in the user’s **Google Calendar**.
   - The user’s **Google Calendar credentials** are required for this integration.

## Code Structure

- **`app.py`**: The main application file that runs the Streamlit interface, integrates voice and chat input, and handles event scheduling.
- **`speech_utils.py`**: Contains functions for handling voice input, including recording and transcription using the **Groq API**.
- **`calendar_utils.py`**: Handles the integration with **Google Calendar** for scheduling events.
- **`llm_utils.py`**: Contains the code for interacting with the **Groq API** to process both text and transcribed speech inputs and extract event details.

## Example Usage

1. **Start the Application**:
   After running `streamlit run app.py`, open the provided URL in your browser.

2. **Interact with the Chatbot**:
   - Type a message to schedule an event, such as **"Schedule a meeting tomorrow at 3 PM"**.
   - Or click the **microphone** button to speak to the chatbot.

3. **Event Confirmation**:
   - The chatbot will display the event details and ask for confirmation.
   - Click **"Yes"** to schedule the event or **"No"** to cancel.

4. **Check Calendar**:
   - Once the event is successfully scheduled, you will receive a confirmation message with event details.

## Contributing

If you'd like to contribute to the project:

1. Fork the repository.
2. Create a new branch.
3. Make your changes and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: Make sure to replace any placeholder text in the code (like API keys) with your actual credentials.
```
