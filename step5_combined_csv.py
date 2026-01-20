from pathlib import Path
import pandas as pd
import os

#%% Change parameters

# Round number
round_number = 1 # Dataset number (e.g. dataset_1) - Run for Each Dataset

# Basic path
basic_path = Path(r'') # CHANGE

# Choose output format:
# 'per_frame' - Keep all individual frame ratings (detailed)
# 'per_video' - Average ratings across all frames in each video (summary)
output_format = 'per_frame'  # CHANGE THIS if you want video-level averages

#%% Combine CSV files from different extra rounds

# Directory containing your CSV files
data_dir = basic_path / f'dataset_{round_number}'

# Get a list of all output CSV files (not combined ones)
csv_files = [f for f in os.listdir(data_dir) 
             if f.startswith('output_') and f.endswith('.csv') and not f.startswith('combined_')]

print(f"Found {len(csv_files)} CSV files to process")

# Read and combine all CSV files
all_dataframes = []

for csv_file in csv_files:
    csv_path = os.path.join(data_dir, csv_file)
    
    # Check if the csv file is not empty
    if os.path.getsize(csv_path) > 0:
        try:
            df = pd.read_csv(csv_path)
            
            if df.empty:
                print(f'CSV file {csv_file} is empty after reading. Skipping.')
                continue
            
            # Add source file column for tracking
            df['source_file'] = csv_file
            all_dataframes.append(df)
            print(f"✓ Loaded {csv_file}: {len(df)} frames")
            
        except pd.errors.EmptyDataError:
            print(f'CSV file {csv_file} has no columns. Skipping.')
            continue
    else:
        print(f'CSV file {csv_file} is empty. Skipping.')

# Combine all dataframes
if all_dataframes:
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    print(f"\n✓ Combined {len(all_dataframes)} files into {len(combined_df)} total frames")
else:
    print("No data to combine!")
    exit()

# Save combined raw data
combined_output_path = os.path.join(data_dir, f'combined_all_rounds_{round_number}.csv')
combined_df.to_csv(combined_output_path, index=False)
print(f"✓ Combined file saved as {combined_output_path}")

#%% Remove duplicates and handle missing data

# Get feature columns (exclude metadata columns)
metadata_cols = ['video', 'frame_number', 'frame_filename', 'source_file']
feature_cols = [col for col in combined_df.columns if col not in metadata_cols]

# Remove duplicate frames (keeping the first occurrence)
print(f"\nChecking for duplicates...")
before_dedup = len(combined_df)
combined_df = combined_df.drop_duplicates(subset=['video', 'frame_number'], keep='first')
after_dedup = len(combined_df)
if before_dedup > after_dedup:
    print(f"✓ Removed {before_dedup - after_dedup} duplicate frames")
else:
    print(f"✓ No duplicates found")

# Check for missing values
missing_count = combined_df[feature_cols].isnull().sum().sum()
print(f"\nMissing feature values: {missing_count}")

#%% Process based on chosen format

if output_format == 'per_frame':
    # Keep per-frame data, just clean it
    print(f"\n=== Per-Frame Output ===")
    
    cleaned_df = combined_df.copy()
    
    # Sort by video name and frame number
    sorted_df = cleaned_df.sort_values(by=['video', 'frame_number'])
    
    # Drop the source_file column (not needed in final output)
    final_df = sorted_df.drop(columns=['source_file'])
    
    print(f"✓ Final dataset: {len(final_df)} frames from {final_df['video'].nunique()} videos")
    
    # Save final per-frame output
    output_path = basic_path / 'average' / 'input' / f'final_output_{round_number}_per_frame.csv'
    os.makedirs(output_path.parent, exist_ok=True)
    final_df.to_csv(output_path, index=False)
    print(f"✓ Saved: {output_path}")

elif output_format == 'per_video':
    # Aggregate frames into video-level averages
    print(f"\n=== Per-Video Output (Averaging Frames) ===")
    
    # Remove frames where ALL features are missing
    cleaned_df = combined_df.dropna(subset=feature_cols, how='all')
    
    # Group by video and calculate mean for each feature
    video_averages = cleaned_df.groupby('video')[feature_cols].mean().reset_index()
    
    # Count frames per video
    frame_counts = cleaned_df.groupby('video').size().reset_index(name='frame_count')
    video_averages = video_averages.merge(frame_counts, on='video')
    
    # Sort by video name
    sorted_df = video_averages.sort_values(by='video')
    
    print(f"✓ Final dataset: {len(sorted_df)} videos")
    print(f"  Average frames per video: {sorted_df['frame_count'].mean():.1f}")
    
    # Save final per-video output
    output_path = basic_path / 'average' / 'input' / f'final_output_{round_number}_per_video.csv'
    os.makedirs(output_path.parent, exist_ok=True)
    sorted_df.to_csv(output_path, index=False)
    print(f"✓ Saved: {output_path}")

else:
    print(f"Error: output_format must be 'per_frame' or 'per_video', not '{output_format}'")

#%% Generate summary statistics

print(f"\n=== Summary Statistics ===")
print(f"Total unique videos: {combined_df['video'].nunique()}")
print(f"Total frames analyzed: {len(combined_df)}")
print(f"Average frames per video: {len(combined_df) / combined_df['video'].nunique():.1f}")

# Show videos with most/least frames
frames_per_video = combined_df.groupby('video').size().sort_values(ascending=False)
print(f"\nVideo with most frames: {frames_per_video.index[0]} ({frames_per_video.iloc[0]} frames)")
print(f"Video with least frames: {frames_per_video.index[-1]} ({frames_per_video.iloc[-1]} frames)")

# Check data completeness
complete_rows = combined_df[feature_cols].notna().all(axis=1).sum()
completion_rate = (complete_rows / len(combined_df)) * 100
print(f"\nData completeness: {completion_rate:.1f}% of frames have all features rated")

print("\n✓ Processing complete!")