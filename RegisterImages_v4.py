import cv2
import pandas as pd
import numpy as np
import os
from glob import glob
import argparse
import re

def read_input_files(dir_file_path, well_tsv_path, channel_tsv_path):
    # Read the list of directories
    with open(dir_file_path, 'r') as file:
        directories = [line.strip() for line in file]
    well_df = pd.read_csv(well_tsv_path, sep='\t', header=None, names=['Well', 'Label'])
    channel_df = pd.read_csv(channel_tsv_path, sep='\t', header=None, names=['channel', 'timepoint', 'descriptor'])
    return directories, well_df, channel_df

def find_image_files(directories, channel_df):
    # Convert the 'timepoint' column to integers to match the loop variable
    channel_df['timepoint'] = channel_df['timepoint'].astype(int)
    images = {}  # {well: {timepoint: {channel: file_path}}}
    well_pattern = re.compile(r"([A-Z][0-9]{1,2})")
    for timepoint, dir_path in enumerate(directories, start=1):
        print(f"Checking directory for timepoint {timepoint}: {dir_path}")
        timepoint_channels = channel_df[channel_df['timepoint'] == timepoint]['channel'].tolist()
        print(f"Channels for timepoint {timepoint}: {timepoint_channels}")
        image_files = glob(os.path.join(dir_path, '*.tif'))
        if not image_files:
            print(f"No image files found in {dir_path}")
            continue
        for image_file in image_files:
            filename = os.path.basename(image_file)
            print(f"Found image file: {filename}")
            well_match = well_pattern.search(filename)
            if well_match:
                well = well_match.group(1)
                images.setdefault(well, {}).setdefault(timepoint, {})
                matched = False
                for channel in timepoint_channels:
                    channel_pattern = re.compile(re.escape(channel), re.IGNORECASE)
                    print(f"Trying to match channel '{channel}' using pattern '{channel_pattern.pattern}' against '{filename}'")
                    if channel_pattern.search(filename):
                        print(f"Matched well: {well}, channel: {channel}")
                        images[well][timepoint][channel] = image_file
                        matched = True
                        break
                if not matched:
                    missing_channels = ', '.join(timepoint_channels)
                    error_message = f"None of the expected channels ({missing_channels}) were found in filename '{filename}' for timepoint {timepoint}."
                    raise ValueError(error_message)
            else:
                print(f"File '{filename}' did not match well pattern.")
    print(f"Total wells found: {len(images)}")
    for well, timepoints in images.items():
        print(f"Well: {well} has {len(timepoints)} timepoints with images.")
    return images

def calculate_and_apply_registration(images, well_df, channel_df, align_channel, output_dir='Aligned'):
    os.makedirs(output_dir, exist_ok=True)
    translation_matrices = {}  # To store translation matrices for each well and timepoint
    # Convert well_df to a dictionary for quick lookup of labels
    well_label_dict = dict(zip(well_df['Well'], well_df['Label']))
    # Convert channel_df to a dictionary for quick lookup of descriptors
    channel_descriptor_dict = {(row['channel'], row['timepoint']): row['descriptor'] for _, row in channel_df.iterrows()}
    for well in images:
        print(f"Processing well: {well}")
        # Get the label for the well
        well_label = well_label_dict.get(well, well)
        ref_image_path = images[well][1].get(align_channel)
        if not ref_image_path:
            raise ValueError(f"{align_channel} channel not found for well {well} at timepoint 1.")
        ref_image = cv2.imread(ref_image_path, cv2.IMREAD_GRAYSCALE)
        sift = cv2.SIFT_create()
        ref_keypoints, ref_descriptors = sift.detectAndCompute(ref_image, None)
        # Loop to save timepoint 1 images directly
        for channel in images[well][1]:
            image_path = images[well][1][channel]
            img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            descriptor = channel_descriptor_dict.get((channel, 1), channel)
            output_filename = os.path.join(output_dir, f'{well_label}_I1_{descriptor}_aligned.tif')
            cv2.imwrite(output_filename, img)
            print(f"Saved timepoint 1 image without translation: {output_filename}")
        for timepoint in sorted(images[well].keys()):
            if timepoint == 1:
                continue
            dapi_image_path = images[well][timepoint].get(align_channel)
            if not dapi_image_path:
                raise ValueError(f"{align_channel} channel not found for well {well} at timepoint {timepoint}.")
            image = cv2.imread(dapi_image_path, cv2.IMREAD_GRAYSCALE)
            cur_keypoints, cur_descriptors = sift.detectAndCompute(image, None)
            matches = cv2.BFMatcher().match(ref_descriptors, cur_descriptors)
            src_pts = np.float32([ref_keypoints[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([cur_keypoints[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
            translation_matrix, _ = cv2.estimateAffinePartial2D(dst_pts, src_pts, method=cv2.RANSAC)
            translation_matrices[(well, timepoint)] = translation_matrix
            matrix_filename = os.path.join(output_dir, f'{well_label}_I{timepoint}_{align_channel}_translation_matrix.npy')
            np.save(matrix_filename, translation_matrix)
            print(f"Saved translation matrix for well {well}, timepoint {timepoint}")
            for channel in images[well][timepoint]:
                image_path = images[well][timepoint][channel]
                img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
                rows, cols = img.shape[:2]
                registered_img = cv2.warpAffine(img, translation_matrix, (cols, rows))
                descriptor = channel_descriptor_dict.get((channel, timepoint), channel)
                output_filename = os.path.join(output_dir, f'{well_label}_I{timepoint}_{descriptor}_aligned.tif')
                cv2.imwrite(output_filename, registered_img)
                print(f"Saved aligned image: {output_filename}")

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Process image alignment inputs.')
    parser.add_argument('--dir_file_path', type=str, required=True, help='Path to the text file containing directory paths.')
    parser.add_argument('--well_tsv_path', type=str, required=True, help='Path to the tab separated file containing well labels.')
    parser.add_argument('--channel_tsv_path', type=str, required=True, help='Path to the tab separated file containing channel descriptors.')
    parser.add_argument('--align_channel', type=str, default='DAPI', help='Channel to use for alignment (default: DAPI).')
    args = parser.parse_args()

    # Assign the arguments to variables
    dir_file_path = args.dir_file_path
    well_tsv_path = args.well_tsv_path
    channel_tsv_path = args.channel_tsv_path
    align_channel = args.align_channel
    directories, well_df, channel_df = read_input_files(dir_file_path, well_tsv_path, channel_tsv_path)
    images = find_image_files(directories, channel_df)
    calculate_and_apply_registration(images, well_df, channel_df, align_channel, output_dir='Aligned')

if __name__ == '__main__':
    main()
#Example Usage
#conda activate opencv (assuming you have an opencv environment with pandas, numpy and opencv installed)
#cd your/file/path
#python RegisterImages_v4.py --dir_file_path directories.txt --well_tsv_path well_labels.tsv --channel_tsv_path channels.tsv --align_channel DAPI
#other notes: 
# for the input files, they should have the file path (or if your current directory already has the file, just the file name)
# well_tsv_path  should be a tab separated file without header. The first column must be the well, the second column must be the descriptor. No quotation marks.
# channel_tsv_path should be a tab separated file without header. The first column must be a channel name which matches exactly the channels in your image file names. The second column should be the order in which the image was taken (ie staining round) starting from 1 for the first image. The third column should be the channel descriptor that you want included in the final registered image name. Once again, no quotes.

