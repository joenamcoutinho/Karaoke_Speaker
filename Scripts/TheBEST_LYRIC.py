import os
from groq import Groq
import os
from dotenv import load_dotenv
from groq import Groq
import json
import logging
import re


# Load environment variables
load_dotenv()
# Initialize the Groq client (you can specify the API key if needed)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Define the path to the MP3 file
filename = r"C:/Users/joenam_tangi0/Desktop/lyrics_speaker/Song/song2.mp3"



with open(filename, "rb") as file:
    transcription = client.audio.transcriptions.create(
        file=(filename, file.read()),
        model="whisper-large-v3",
        response_format="verbose_json",
    )

    # Full transcription text
    print("Full Transcription:")
    # print(type(transcription))  # Check the type
    # print(dir(transcription))   # List the attributes and methods of the object
    # print(transcription)  # Use dot notation to access 'text' attribute
    transcription_dict = transcription.to_dict()
    segments = transcription_dict['segments']
    print(segments)


# Prepare the data for JSON output (you can modify this to include/exclude other fields)
output_data = []

for segment in segments:
    segment_data = {
        'id': segment['id'],
        'seek': segment['seek'],
        'start': segment['start'],
        'end': segment['end'],
        'text': segment['text'],
        'tokens': segment['tokens'],
        'temperature': segment['temperature'],
        'avg_logprob': segment['avg_logprob'],
        'compression_ratio': segment['compression_ratio'],
        'no_speech_prob': segment['no_speech_prob']
    }
    output_data.append(segment_data)

# Specify the file path where you want to save the JSON file
output_file = 'transcription_segments.json'

# Write the data to the JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print(f"Transcription saved to {output_file}")


   