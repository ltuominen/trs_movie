import os
import time
from faster_whisper import WhisperModel
import pandas as pd

#%% Change parameters
folder_path = ""

#%% Initialize local Whisper model
print("Loading Whisper model (first time may take a few minutes)...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("✓ Model loaded!\n")

#%% Transcribe functions

def transcribe_audio(file_path):
    """ Transcribe audio using local Faster Whisper """
    segments, info = model.transcribe(file_path, beam_size=5)
    
    # Combine all segments into full text
    transcript = " ".join([segment.text for segment in segments])
    return transcript

def process_audio_files(folder_path, processed_file='audio_processed.txt'):
    start_time = time.time()
    
    # Read the list of files already processed
    try:
        with open(processed_file, 'r') as f:
            processed_files = [line.strip() for line in f]
    except FileNotFoundError:
        processed_files = []

    processed_count = 0
    error_count = 0
    
    # Loop through all items in the folder
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        
        # Check if it's an audio file
        if os.path.isfile(item_path) and item.lower().endswith(('.mp3', '.wav', '.m4a')) and item not in processed_files:
            print(f"\n🎵 Processing: {item}")
            
            try:
                # Transcribe the file
                transcript_text = transcribe_audio(item_path)          
                
                # Save transcription as a text file
                base_name = os.path.splitext(item)[0]
                text_file_path = os.path.join(folder_path, base_name + '.txt')
                
                with open(text_file_path, 'w', encoding='utf-8') as text_file:
                    text_file.write(transcript_text)
                
                # Save progress
                with open(processed_file, 'a', encoding='utf-8') as f:
                    f.write(item + '\n')
                
                processed_count += 1
                print(f"✓ Saved: {base_name}.txt")
                
            except Exception as e:
                error_count += 1
                print(f"✗ Error: {e}")
                
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✓ Processed: {processed_count} files")
    print(f"✗ Errors: {error_count} files")
    print(f"⏱️ Total time: {total_time:.2f} sec.")
    print(f"{'='*60}")

#%% Load transcripts into DataFrame
def load_transcriptions_to_dataframe(folder_path):
    data = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                transcription = file.read()
            data.append({'file_name': filename, 'transcription': transcription})
    
    return pd.DataFrame(data)

# Start processing
process_audio_files(folder_path)

# Load results
df_transcriptions = load_transcriptions_to_dataframe(folder_path)
print(f"\n📊 Loaded {len(df_transcriptions)} transcriptions into DataFrame")