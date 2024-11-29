import time
import pygame
import librosa
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Function to scrape lyrics from Genius.com
def scrape_genius_lyrics(song_title, artist):
    # Setup Chrome WebDriver with options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Construct Genius search URL
        search_url = f"https://genius.com/search?q={song_title} {artist}"
        driver.get(search_url)
        
        # Wait and handle cookie consent if present
        try:
            cookie_accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'agree')]"))
            )
            cookie_accept_button.click()
            time.sleep(2)  # Small pause after accepting cookies
        except:
            print("No cookie consent found or couldn't click")
        
        # Find and click on first search result
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.mini_card"))
        )
        
        if results:
            first_result = results[0]
            first_result.click()
            
            # Wait for lyrics container
            lyrics_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'lyrics') or contains(@class, 'Lyrics')]"))
            )
            
            # Extract lyrics
            lyrics = lyrics_container.text
            
            # Pause briefly before closing
            time.sleep(2)
            
            return lyrics
        
    except Exception as e:
        print(f"Error scraping lyrics: {e}")
        return None
    
    finally:
        driver.quit()

# Function to break lyrics into lines
def break_lyrics(lyrics):
    # Split the lyrics into lines based on newlines or other punctuation
    return [line.strip() for line in lyrics.split('\n') if line.strip()]

# Function to get beat times from the song using librosa
def get_beat_times(song_file):
    y, sr = librosa.load(song_file)  # Load the song
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    beats, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)
    return beat_times

# Function to display lyrics in sync with the song using the generated timestamps
def display_lyrics_with_timing(lyrics, song_file, beat_times):
    # Initialize pygame
    pygame.mixer.init()
    pygame.mixer.music.load(song_file)
    pygame.mixer.music.play()

    # Initialize pygame screen and font
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Karaoke Lyrics")
    font = pygame.font.SysFont("Arial", 36)
    clock = pygame.time.Clock()

    # Break lyrics into lines
    lines = break_lyrics(lyrics)
    
    # Calculate the number of lines of lyrics and the number of beats
    num_lyrics = len(lines)
    num_beats = len(beat_times)
    
    # The number of beats should match the number of lines or be adjusted accordingly
    if num_lyrics > num_beats:
        print("Warning: More lyrics than beats, syncing will be approximated.")
    elif num_lyrics < num_beats:
        print("Warning: More beats than lyrics, syncing will be approximated.")

    current_line = 0
    start_time = time.time()

    while pygame.mixer.music.get_busy() and current_line < num_lyrics:
        # Check for quit events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        elapsed_time = time.time() - start_time

        # Display lyrics when the timestamp matches the elapsed time
        if current_line < num_beats and elapsed_time >= beat_times[current_line]:
            screen.fill((0, 0, 0))  # Clear the screen
            text_surface = font.render(lines[current_line], True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(400, 300))
            screen.blit(text_surface, text_rect)
            pygame.display.flip()  # Update the display
            current_line += 1  # Move to the next line

        clock.tick(30)  # Frame rate limit

    pygame.quit()

def main():
    song_title = "Bohemian Rhapsody"
    artist = "Queen"
    song_file = "C:/Users/joenam_tangi0/Desktop/lyrics_speaker/song.mp3"  # Path to your song file

    # Scrape lyrics
    lyrics = scrape_genius_lyrics(song_title, artist)
    if lyrics:
        print("Lyrics fetched successfully!")
        print(lyrics)

        # Get the beat times from the song
        beat_times = get_beat_times(song_file)

        # Display lyrics in sync with the beats and TTS
        display_lyrics_with_timing(lyrics, song_file, beat_times)
    else:
        print("Failed to fetch lyrics.")

if __name__ == '__main__':
    main()
