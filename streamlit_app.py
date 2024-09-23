import streamlit as st
import asyncio
from duckduckgo_search import DDGS
import edge_tts
from pydub import AudioSegment
import io
import tempfile
import os

class Agent:
    def __init__(self, role, backstory, voice):
        self.role = role
        self.backstory = backstory
        self.voice = voice

    def generate_response(self, prompt):
        full_prompt = f"{self.backstory}\n\nAs the {self.role}, {prompt} Remember, you're simulating a podcast, so keep the conversation natural and engaging."
        with DDGS() as ddgs:
            response = ddgs.chat(full_prompt, model="gpt-4o-mini")
        return response

async def text_to_speech(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.write(chunk["data"])
    audio_data.seek(0)
    return AudioSegment.from_mp3(audio_data)

def clean_dialogue(text, role):
    with DDGS() as ddgs:
        prompt = f"""Clean and format the following {role} dialogue for a podcast:
        1. Remove any metadata or role labels.
        2. Eliminate any repetitions or redundant information.
        3. Ensure the dialogue is concise and to the point.
        4. Only return the cleaned dialogue.

        Original text:
        {text}"""
        cleaned_text = ddgs.chat(prompt, model="gpt-4o-mini")
    return cleaned_text.strip()

async def simulate_podcast(topic):
    host = Agent(
        role='Podcast Host',
        backstory=f"""You're an AI simulating a friendly and curious podcast host. You're known for 
        your insightful questions and ability to guide conversations.""",
        voice="en-US-GuyNeural"
    )

    guest = Agent(
        role='Expert Guest',
        backstory=f"""You're an AI simulating an expert in {topic}. You have extensive knowledge 
        and experience in this field. You're here to share insights and discuss {topic} in an 
        informative yet approachable manner.""",
        voice="en-US-JennyNeural"
    )

    transcript = ""
    combined_audio = AudioSegment.silent(duration=500)  # Start with 0.5 second of silence
    conversation_history = ""

    # Discussion
    for i in range(4):  # 4 exchanges
        host_prompt = f"Ask a new, unique question about {topic} that hasn't been discussed yet. Consider the conversation history: {conversation_history}"
        host_question = host.generate_response(host_prompt)
        cleaned_host_question = clean_dialogue(host_question, "host")
        transcript += f"Host: {cleaned_host_question}\n\n"
        combined_audio += await text_to_speech(cleaned_host_question, host.voice)
        conversation_history += f"Host: {cleaned_host_question}\n"

        guest_prompt = f"Respond to the host's question: {cleaned_host_question}\nProvide a unique perspective, considering the conversation history: {conversation_history}"
        guest_response = guest.generate_response(guest_prompt)
        cleaned_guest_response = clean_dialogue(guest_response, "guest")
        transcript += f"Guest: {cleaned_guest_response}\n\n"
        combined_audio += await text_to_speech(cleaned_guest_response, guest.voice)
        conversation_history += f"Guest: {cleaned_guest_response}\n"

    # Save the audio
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
        combined_audio.export(temp_audio.name, format="mp3")
        st.audio(temp_audio.name, format='audio/mp3')
    
    # Display and offer transcript download
    st.text_area("Transcript", transcript, height=300)
    st.download_button(
        label="Download Transcript",
        data=transcript,
        file_name=f"podcast_{topic.replace(' ', '_')}_transcript.txt",
        mime="text/plain"
    )

    # Clean up temporary file
    os.unlink(temp_audio.name)

st.title("AI Podcast Simulator")
topic = st.text_input("What topic would you like discussed in the podcast?")

if topic:
    if st.button("Generate Podcast"):
        asyncio.run(simulate_podcast(topic))
