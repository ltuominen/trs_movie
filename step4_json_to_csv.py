from pathlib import Path
import json
import pandas as pd
import numpy as np
import re
import shutil
import os

#%% Change parameters

# This parameter is the number of your dataset you are currently working with
round_number = 1 # Dataset number (e.g. dataset_1)

# If you have extra round(s) in your dataset, change this value
extra_round = 0 # This value is default

# Basic path
basic_path = Path(r'') # CHANGE

# Image source folder and next round target folder
source_folder = 'path/stimulus_frames' # CHANGE
target_folder = f'path/stimulus_frames_round_{round_number}_{extra_round}' # CHANGE

#%% Convert json file to csv file

file_path = basic_path / f'dataset_{round_number}/output_{round_number}_{extra_round}.json'

# Function to read a JSON string and extract the desired content (per-frame version)
def load_and_extract(file_path):
    extracted_data = []
    
    # Open the file and read line by line
    with open(file_path, 'r', encoding='utf-8') as file:
        json_object = ''
        for line in file:
            json_object += line.strip()
            if line.startswith('}'):  # Checks if the line indicates the end of a JSON object
                try:
                    # Parse the JSON object
                    data = json.loads(json_object)
                    # Reset the JSON object string
                    json_object = ''
                    
                    # Check if this is a video object with frames
                    if 'subfolder' in data and 'frames' in data:
                        subfolder = data['subfolder']
                        
                        # Process each frame
                        for frame_data in data['frames']:
                            frame_number = frame_data.get('frame_number', 'unknown')
                            frame_filename = frame_data.get('frame_filename', 'unknown')
                            
                            # Extract content from the response
                            response = frame_data.get('response', {})
                            
                            if 'error' in response:
                                content = response['error'].get('message', '')
                            elif 'choices' in response and len(response['choices']) > 0:
                                content = response['choices'][0]['message']['content']
                            else:
                                content = ''
                            
                            # Store with metadata
                            extracted_data.append({
                                'video': subfolder,
                                'frame_number': frame_number,
                                'frame_filename': frame_filename,
                                'content': content
                            })
                    
                    # Handle old format (single video response) for backwards compatibility
                    elif 'error' in data:
                        content = data['error'].get('message', '')
                        extracted_data.append({
                            'video': 'unknown',
                            'frame_number': 0,
                            'frame_filename': 'unknown',
                            'content': content
                        })
                    elif 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        extracted_data.append({
                            'video': 'unknown',
                            'frame_number': 0,
                            'frame_filename': 'unknown',
                            'content': content
                        })
                        
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    # Reset the JSON object string in case of a decoding error
                    json_object = ''

    return extracted_data

# Load and extract the contents of the JSON file
extracted_data = load_and_extract(file_path)

# FIXED: Function for parsing individual text content
def parse_content(content):
    """
    Parse content in format: "Feature: Score"
    Example: "Dominant: 10  \nUnpleasant: 80"
    """
    # Check if the content is unavailable or empty
    if not content or content.strip().startswith("{I'm sorry}"):
        return {"Data Unavailable": np.nan}

    # Split the content string into lines
    lines = content.split('\n')
    
    # Prepare a dictionary to hold the feature-score pairs
    feature_scores = {}
    
    # FIXED: Simplified regex for "Feature: Score" format with flexible whitespace
    # This matches: "Feature: 10", "Feature: 10  ", "Feature:10", etc.
    line_regex = re.compile(r'^([^:]+):\s*(\d+)\s*$')
    
    parsed_count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = line_regex.match(line)
        if match:
            feature, score = match.groups()
            try:
                # Convert score to float and store in the dictionary
                feature_scores[feature.strip()] = float(score)
                parsed_count += 1
            except ValueError:
                # Handle the case where conversion fails
                feature_scores[feature.strip()] = np.nan
    
    # Optional: Print warning if very few features were parsed
    if parsed_count == 0 and len(lines) > 5:
        print(f"Warning: No features parsed from content with {len(lines)} lines")
        print(f"First line sample: '{lines[0][:100]}'")
    
    return feature_scores if feature_scores else {"Data Unavailable": np.nan}

# Parse all extracted content and combine with metadata
parsed_data = []
for item in extracted_data:
    parsed_features = parse_content(item['content'])
    # Combine metadata with parsed features
    row_data = {
        'video': item['video'],
        'frame_number': item['frame_number'],
        'frame_filename': item['frame_filename'],
        **parsed_features  # Unpack all feature scores
    }
    parsed_data.append(row_data)

# Create a DataFrame from the results
df = pd.DataFrame(parsed_data)

# Save the DataFrame as a CSV file
output_csv_path = basic_path / f'dataset_{round_number}/output_{round_number}_{extra_round}.csv'
df.to_csv(output_csv_path, index=False)

print(f"✓ CSV file created: {output_csv_path}")
print(f"  Total frames processed: {len(df)}")
print(f"  Unique videos: {df['video'].nunique()}")
print(f"  Total columns (features): {len(df.columns)}")
print(f"  Feature columns: {len([col for col in df.columns if col not in ['video', 'frame_number', 'frame_filename']])}")

#%% Check missing frames and copy videos to new folder

# Find rows where all feature values are missing (excluding metadata columns)
feature_columns = [col for col in df.columns if col not in ['video', 'frame_number', 'frame_filename']]
empty_rows = df.index[df[feature_columns].isnull().all(axis=1)].tolist()

# Find rows with at least one missing feature value
nan_rows = df.index[df[feature_columns].isnull().any(axis=1)].tolist()

# Create a DataFrame containing only rows with at least one missing value
nan_rows_df = df[df[feature_columns].isnull().any(axis=1)]

# Find feature columns with at least one missing value
columns_with_null = df[feature_columns].columns[df[feature_columns].isnull().any()].tolist()

# Find feature columns with all values missing
all_null_columns = df[feature_columns].columns[df[feature_columns].isnull().all()].tolist()

print(f"\n=== Missing Data Summary ===")
print(f"Frames with all features missing: {len(empty_rows)}")
print(f"Frames with some features missing: {len(nan_rows)}")
print(f"Features with some missing values: {len(columns_with_null)}")
print(f"Features with all missing values: {len(all_null_columns)}")

if all_null_columns:
    print(f"\nFeatures with all values missing:")
    for col in all_null_columns[:10]:  # Show first 10
        print(f"  - {col}")

# Get unique videos that have frames with missing data
videos_with_missing_frames = df.loc[empty_rows, 'video'].unique().tolist()

print(f"\nVideos with completely missing frames: {len(videos_with_missing_frames)}")

# Copy videos with missing frames to target folder for reprocessing
if videos_with_missing_frames:
    os.makedirs(target_folder, exist_ok=True)
    
    for video_name in videos_with_missing_frames:
        source_path = os.path.join(source_folder, video_name)
        target_path = os.path.join(target_folder, video_name)
        
        # If the source folder exists, copy it to the target folder
        if os.path.exists(source_path):
            if not os.path.exists(target_path):  # Avoid overwriting
                shutil.copytree(source_path, target_path)
                print(f"✓ '{video_name}' has been copied to '{target_folder}'.")
            else:
                print(f"⚠ '{video_name}' already exists in '{target_folder}', skipping.")
        else:
            print(f"✗ '{video_name}' not found in '{source_folder}'.")
else:
    print("\n✓ No videos need reprocessing!")

# Optionally save a list of videos needing reprocessing
if videos_with_missing_frames:
    reprocess_list_path = basic_path / f'dataset_{round_number}/videos_to_reprocess_{round_number}_{extra_round}.txt'
    with open(reprocess_list_path, 'w') as f:
        for video in videos_with_missing_frames:
            f.write(f"{video}\n")
    print(f"\n✓ List of videos to reprocess saved to: {reprocess_l}")