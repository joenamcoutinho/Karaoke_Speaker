import os
from dotenv import load_dotenv
from groq import Groq
import json
import logging
import re
from bs4 import BeautifulSoup
import requests
from rapidfuzz import process, fuzz




# Load environment variables
load_dotenv()
# Initialize the Groq client (you can specify the API key if needed)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))



# Function to fetch lyrics from Genius API
def fetch_lyrics(song_title, artist_name, access_token):
    search_url = "https://api.genius.com/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"q": f"{song_title} {artist_name}"}
    
    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error fetching lyrics: {response.status_code}")
        return None
    
    hits = response.json()['response']['hits']
    if not hits:
        print("No results found on Genius.")
        return None
    
    # Fetch the first match's URL
    song_path = hits[0]['result']['path']
    lyrics_url = f"https://genius.com{song_path}"
    
    # Scrape lyrics (Genius API does not provide lyrics directly)
    response = requests.get(lyrics_url)
    if response.status_code != 200:
        print(f"Error fetching lyrics page: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    lyrics_div = soup.find('div', class_='lyrics') or soup.find('div', class_='Lyrics__Root-sc-1ynbvzw-0')
    if not lyrics_div:
        print("Lyrics not found on Genius page.")
        return None
    
    # Extract and clean lyrics
    raw_lyrics = lyrics_div.get_text(separator='\n')
    cleaned_lyrics = clean_lyrics(raw_lyrics)  # Use the enhanced cleaning function
    return cleaned_lyrics

def clean_lyrics(raw_lyrics):
    cleaned_lyrics = []
    for line in raw_lyrics.splitlines():
        line = line.strip()

        # Skip lines that are purely metadata or annotations
        if not line or line.startswith(('[', '(')) or any(keyword in line.lower() for keyword in ["contributor", "embed", "you might also like", "lyrics"]):
            continue
        if re.match(r'^\d+$', line) or len(line.split()) < 2:  # Skip single words or numbers
            continue

        cleaned_lyrics.append(line)

    return cleaned_lyrics

# Function to align and correct transcription
def align_and_correct(transcription_segments, genius_lyrics):
    """
    Aligns transcription segments with Genius lyrics and corrects mismatched text.
    """
    corrected_segments = []
    genius_text = " ".join(genius_lyrics) # Combines all genius lyrics into one string
    genius_lyrics_chunks = split_lyrics(genius_lyrics)  # Break Genius lyrics into chunks
    genius_index = 0 # Track progress in Genius lyrics

    for segment in transcription_segments:
        original_text = segment['text']
        
        
        # Match transcription text to the best chunk from Genius lyrics
        best_match, score, _ = process.extractOne(
            original_text, genius_lyrics_chunks, scorer=fuzz.token_sort_ratio
        )
        # Print the match and score
        print(f"Original: {original_text}")
        print(f"Best Match: {best_match}")
        print(f"Score: {score}\n")

        if score > 80:  # Only replace if the similarity score is above 75
            print(f"Replacing:\n  Original: {original_text}\n  Genius: {best_match}\n")
            segment['text'] = best_match
        
        corrected_segments.append(segment)
    
    return corrected_segments


def split_lyrics(lyrics):
    """
    Splits Genius lyrics into smaller chunks for better matching.
    """
    chunks = []
    current_chunk = []
    for line in lyrics:
        # Add each line to the chunk
        current_chunk.append(line)
        # Every sentence or after a few lines, break the chunk (optional)
        if len(" ".join(current_chunk)) > 60:  # Group lines until a reasonable chunk size # Reduce chunk size for better granularity
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    if current_chunk:  # Add any remaining lines as a chunk
        chunks.append(" ".join(current_chunk))
    return chunks

# Main Script

if __name__ == "__main__":
    # Define the path to the MP3 file
    filename = r"C:/Users/joenam_tangi0/Desktop/lyrics_speaker/Song/song2.mp3"

    # Replace with your Genius API token
    
    # Load Genius API credentials
    CLIENT_ID = os.environ.get("GENIUS_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("GENIUS_CLIENT_SECRET")
    ACCESS_TOKEN = os.environ.get("GENIUS_ACCESS_TOKEN")  # Access token should be generated already.
        
    # Replace with the song's title and artist
    song_title = "Sprinter"
    artist_name = "Central"



    # Transcribe audio

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
        
        
        # Convert transcription to a dictionary
        transcription_dict = transcription.to_dict()
        segments = transcription_dict['segments']
        #print(segments)


    # Fetch Genius lyrics
    genius_lyrics = fetch_lyrics(song_title, artist_name, ACCESS_TOKEN)
    # print("Genius Lyrics" , genius_lyrics)
    
    if genius_lyrics:
        # Align and correct transcription
        corrected_segments = align_and_correct(segments, genius_lyrics)
    else:
        corrected_segments = segments



    # Prepare the data for JSON output (you can modify this to include/exclude other fields)
    output_data = []

    for segment in corrected_segments:
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
    output_file = 'corrected_transcription_segments.json'

    # Write the data to the JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(f"Transcription saved to {output_file}")


   