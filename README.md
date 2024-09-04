# CycIF Image Registration Tool

This script, `ImageRegistration_v4.py`, provides a tool for aligning and registering images from multiple rounds of cyclic immunofluorescence staining based on a user-specified channel which is the same staining across all cycles. This would generally be a nuclear dye (the default is `DAPI`). The tool uses SIFT keypoints and a rigid affine transformation to align images images from latter cycles back to the first cycle.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Example](#example)
- [Command Line Arguments](#command-line-arguments)
- [Input File Format](#input-file-format)
- [Output](#output)
- [Contributing](#contributing)
- [License](#license)

## Installation

To install and run the image alignment tool, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/djhfknapp/CycIF_ImageRegistration.git
   cd CycIF_ImageRegistration
   ```

2. **Set Up a Virtual Environment** (Recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. **Install Required Packages**:
   Install the necessary Python packages listed in `requirements.txt`.
   ```bash
   pip install -r requirements.txt
   ```

   If you don't have a `requirements.txt` file, create it with the following content:
   ```
   opencv-python
   numpy
   pandas
   ```

## Usage

To use the image alignment tool, run the script from the command line with the required arguments:

```bash
python ImageRegistration_v4.py --dir_file_path directories.txt --well_tsv_path well_labels.tsv --channel_tsv_path channels.tsv [--align_channel CHANNEL]
```

### Example

```bash
python ImageRegistration_v4.py --dir_file_path directories.txt --well_tsv_path well_labels.tsv --channel_tsv_path channels.tsv --align_channel DAPI
```

### Command Line Arguments

- `--dir_file_path`: Path to the text file containing directory paths. The order of these must match the order of the cycles (all images will be aligned to those from the first directory) **(Required)**
- `--well_tsv_path`: Path to the TSV file containing well labels. **(Required)**
- `--channel_tsv_path`: Path to the TSV file containing channel descriptors. **(Required)**
- `--align_channel`: Channel to use for alignment. Default is `DAPI`. **(Optional)**

## Input File Format

- **Directory Paths (`directories.txt`)**: A text file with each line specifying the path to a directory containing images.

- **Well Labels (`well_labels.tsv`)**: A tab-separated file without a header. Each line should contain:
  - **First column**: Well (e.g., `B2`, `C3`).
  - **Second column**: Descriptor for the well (e.g., `N3`, `Control`).

  Example:
  ```
  B2    N3
  C3    Control
  ```

- **Channel Descriptors (`channels.tsv`)**: A tab-separated file without a header. Each line should contain:
  - **First column**: Channel name that matches exactly with the channel names in your image filenames (e.g., `DAPI`, `CY5`).
  - **Second column**: Timepoint or order of the image taken (staining round), starting from 1 (e.g., `1`, `2`).
  - **Third column**: Descriptor for the channel to include in the final registered image name (e.g., `Nucleus`, `SOX4`).

  Example:
  ```
  DAPI    1    Nucleus
  CY5     2    SOX4
  ```
## Contributing

We welcome contributions to enhance the functionality and usability of this tool. To contribute:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add new feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
