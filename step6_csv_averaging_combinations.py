import os
import pandas as pd
import glob
from itertools import combinations

#%% Change parameters

# Number of files
number_of_files = 5

# Input and output directory
input_dir = r'' #CHANGE
output_dir = r'' #CHANGE

#%% Script

# Reading all CSV files from directory
csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
csv_files.sort()

# Check number of csv files
assert len(csv_files) == number_of_files, f"Expected {number_of_files} files, but found {len(csv_files)}"

# FIXED: Average function for per-frame structure
def process_files(files):
    dfs = []
    
    # Metadata columns (these will NOT be averaged)
    metadata_columns = ['video', 'frame_number', 'frame_filename']
    
    for i, file in enumerate(files):
        df = pd.read_csv(file)
        
        # Verify metadata columns exist
        if i == 0:
            if not all(col in df.columns for col in metadata_columns):
                raise ValueError(f"Expected metadata columns {metadata_columns} not found in {file}")
        
        # Store the dataframe
        dfs.append(df)
    
    # Take metadata from the first file
    metadata_df = dfs[0][metadata_columns].copy()
    
    # Extract only feature columns (everything except metadata) from all files
    feature_dfs = []
    for df in dfs:
        # Get only the feature columns (exclude metadata)
        feature_cols = [col for col in df.columns if col not in metadata_columns]
        feature_dfs.append(df[feature_cols])
    
    # Concatenate all feature dataframes along columns (side by side)
    # This creates a dataframe where each feature appears multiple times (once per file)
    combined_features = pd.concat(feature_dfs, axis=1)
    
    # Group by column names and calculate mean
    # This averages all columns with the same name across different files
    # Transpose, group, mean, then transpose back to fix deprecation warning
    averaged_features = combined_features.T.groupby(level=0).mean().T
    
    # Combine metadata with averaged features
    final_df = pd.concat([metadata_df, averaged_features], axis=1)
    
    return final_df

loop_end_num = number_of_files + 1
loop_start_num = loop_end_num - number_of_files

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

print(f"\n=== Starting averaging process ===")
print(f"Input directory: {input_dir}")
print(f"Output directory: {output_dir}")
print(f"Number of CSV files found: {len(csv_files)}")
print(f"Files: {[os.path.basename(f) for f in csv_files]}\n")

# Loop over 2, 3, 4, and 5 files (or whatever range you specified)
for n_files in range(loop_start_num, loop_end_num):
    print(f"\n--- Processing combinations of {n_files} files ---")
    
    # Generate all combinations of n_files from the list of CSV files
    combo_count = 0
    for selected_files in combinations(csv_files, n_files):
        result_df = process_files(selected_files)
        
        # Create the output filename
        # Get the file indices (+1 to make them 1-based)
        selected_files_indices = [csv_files.index(f) + 1 for f in selected_files]
        
        # Join the indices into a string separated by underscores
        selected_files_str = "_".join(map(str, selected_files_indices))
        
        # Create the filename with n_files and the selected files' indices
        output_filename = f'output_average_{n_files}_files_{selected_files_str}.csv'
        
        # Save the result to the output directory
        output_path = os.path.join(output_dir, output_filename)
        result_df.to_csv(output_path, index=False)
        
        combo_count += 1
        print(f"  ✓ [{combo_count}] Files {selected_files_indices} → {output_filename}")
        print(f"      Rows: {len(result_df)}, Columns: {len(result_df.columns)} (3 metadata + {len(result_df.columns)-3} features)")

print(f"\n=== Averaging complete ===")
print(f"All output files saved to: {output_dir}")