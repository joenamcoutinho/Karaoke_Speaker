import os
from dotenv import load_dotenv
from groq import Groq
import json
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Load environment variables
load_dotenv()

def generate_smart_timestamps(text):
    """
    Generate more accurate timestamps by adjusting word durations 
    based on the song's rhythm and phrase groupings.
    
    Args:
        text (str): Transcribed text
    
    Returns:
        list: List of dictionaries with smart timestamps
    """
    def split_into_groups(text):
        """
        Split the transcription text into smaller groups based on lyric lines.
        Each line represents a natural break in the song.
        """
        # Assume that the song's structure splits naturally by punctuation or key phrases
        groups = re.split(r'(?<=\w[.!?])|\b(?:oh|so|well|uh|ah)\b', text)
        groups = [group.strip() for group in groups if group.strip()]
        return groups

    groups = split_into_groups(text)
    timestamps = []

    current_time = 0.0
    word_duration = 0.12  # Faster word duration for tighter timing
    base_pause_duration = 0.25  # Small pauses between lines

    for group in groups:
        # Count words in the group
        words = re.findall(r'\b\w+\b', group)
        group_duration = len(words) * word_duration

        # Create timestamp entry for the group
        timestamp_entry = {
            'text': group,
            'start': current_time,
            'end': current_time + group_duration,
            'words': words
        }

        timestamps.append(timestamp_entry)

        # Apply dynamic pauses
        pause_duration = base_pause_duration
        if len(words) > 6:
            pause_duration = base_pause_duration + 0.2  # Increase pause for longer phrases

        current_time += group_duration + pause_duration

    return timestamps

def transcribe_audio_with_smart_timestamps(file_path):
    """
    Transcribe an audio file and generate smart timestamps.
    
    Args:
        file_path (str): Path to the MP3 audio file
    
    Returns:
        dict: Transcription result with smart timestamps
    """
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Initialize Groq client
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        # Transcribe audio
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="json"
            )

        # Convert transcription to dictionary
        transcription_dict = transcription.model_dump()

        # Generate smart timestamps
        smart_timestamps = generate_smart_timestamps(transcription_dict.get('text', ''))

        # Add timestamps to transcription dictionary
        transcription_dict['smart_timestamps'] = smart_timestamps

        # Export transcription to JSON
        output_json = os.path.splitext(file_path)[0] + '_smart_transcription.json'
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(transcription_dict, f, ensure_ascii=False, indent=2)

        logging.info(f"Transcription with smart timestamps saved to {output_json}")
        return transcription_dict

    except Exception as e:
        logging.error(f"Transcription error: {e}")
        raise

def main():
    # Example usage
    audio_file_path = r"C:/Users/joenam_tangi0/Desktop/lyrics_speaker/Song/song.mp3"

    try:
        result = transcribe_audio_with_smart_timestamps(audio_file_path)

        # Print timestamps
        print("Smart Timestamps:")
        for timestamp_group in result.get('smart_timestamps', []):
            print(f"Group: {timestamp_group['text']}")
            print(f"  Start: {timestamp_group['start']} seconds")
            print(f"  End: {timestamp_group['end']} seconds")
            print("  Words:", timestamp_group['words'])
            print()

    except Exception as e:
        logging.error(f"Process failed: {e}")

if __name__ == "__main__":
    main()
