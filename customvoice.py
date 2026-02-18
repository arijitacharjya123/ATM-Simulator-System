import base64
import requests
import json
import google.auth
import google.auth.transport.requests

# --- CONFIGURATION ---
PROJECT_ID = "YOUR_GOOGLE_CLOUD_PROJECT_ID" # Replace with your Project ID
LOCATION = "global" # or your specific region
API_ENDPOINT = f"{LOCATION}-texttospeech.googleapis.com" if LOCATION != "global" else "texttospeech.googleapis.com"

# --- AUTHENTICATION ---
# Automatically find credentials from your environment
credentials, _ = google.auth.default()
authentication = google.auth.transport.requests.Request()
credentials.refresh(authentication)
ACCESS_TOKEN = credentials.token

# --- HELPER FUNCTIONS ---

def wav_to_base64(file_path):
    """Reads a WAV file and converts it to a base64 string."""
    try:
        with open(file_path, "rb") as wav_file:
            return base64.b64encode(wav_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def create_voice_key(reference_path, consent_path):
    """Generates the cloning key using the reference and consent audio."""
    ref_b64 = wav_to_base64(reference_path)
    consent_b64 = wav_to_base64(consent_path)

    if not ref_b64 or not consent_b64:
        return None

    url = f"https://{API_ENDPOINT}/v1beta1/voices:generateVoiceCloningKey"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "x-goog-user-project": PROJECT_ID,
        "Content-Type": "application/json; charset=utf-8",
    }

    request_body = {
        "reference_audio": {
            "audio_config": {"audio_encoding": "LINEAR16", "sample_rate_hertz": 24000},
            "content": ref_b64,
        },
        "voice_talent_consent": {
            "audio_config": {"audio_encoding": "LINEAR16", "sample_rate_hertz": 24000},
            "content": consent_b64,
        },
        # This script text must match the audio in consent.wav exactly
        "consent_script": "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model.",
        "language_code": "en-US",
    }

    response = requests.post(url, headers=headers, json=request_body)
    
    if response.status_code == 200:
        return response.json().get("voiceCloningKey")
    else:
        print(f"Error creating key: {response.text}")
        return None

def speak_with_clone(voice_key, text_to_say):
    """Synthesizes speech using the generated voice key."""
    url = f"https://{API_ENDPOINT}/v1beta1/text:synthesize"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "x-goog-user-project": PROJECT_ID,
        "Content-Type": "application/json; charset=utf-8",
    }

    request_body = {
        "input": {"text": text_to_say},
        "voice": {
            "language_code": "en-US",
            "voice_clone": {
                "voice_cloning_key": voice_key, 
            },
        },
        "audioConfig": {"audioEncoding": "LINEAR16", "sample_rate_hertz": 24000},
    }

    response = requests.post(url, headers=headers, json=request_body)
    
    if response.status_code == 200:
        audio_content = response.json().get("audioContent")
        if audio_content:
            # Save the audio to a file
            with open("agent_output.wav", "wb") as f:
                f.write(base64.b64decode(audio_content))
            print("Success! Audio saved to 'agent_output.wav'")
    else:
        print(f"Error synthesizing text: {response.text}")

# --- EXECUTION ---

# 1. Define your file paths
ref_audio = "path/to/your/reference.wav" 
consent_audio = "path/to/your/consent.wav"

# 2. Generate the Key
print("Generating Voice Key...")
cloning_key = create_voice_key(ref_audio, consent_audio)

# 3. Use the Key to Speak
if cloning_key:
    print(f"Voice Key Created: {cloning_key[:10]}...") 
    text = "Hello, I am your new AI voice agent. How can I help you?"
    speak_with_clone(cloning_key, text)
