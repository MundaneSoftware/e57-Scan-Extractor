# E57 Scan Extractor

E57 Scan Extractor is a Python-based tool for processing `.e57` LiDAR scan files, cropping points based on a specified bounding radius, applying thinning logic to reduce point density, and exporting the processed scans as `.laz` files. The tool includes a user-friendly GUI for file selection and parameter configuration.

## Features

- **Batch Processing**: Process multiple `.e57` files in one go.
- **Bounding Radius Cropping**: Filters points based on a user-defined radius around the scan's origin.
- **Thinning**: Reduces point density while preserving the spatial distribution of points.
- **LAZ Export**: Saves the processed scans in `.laz` format, compatible with various GIS and 3D applications.
- **GUI**: Intuitive interface using `tkinter` for selecting files and setting parameters.

## Prerequisites

### Required Libraries
Ensure the following Python libraries are installed:

- `numpy`
- `pye57`
- `laspy`
- `scipy`
- `tkinter` (comes pre-installed with Python)

You can install the required libraries using pip:

```bash
pip install numpy pye57 laspy scipy
```

### Python Version
This tool requires Python 3.8 or higher.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/MundaneSoftware/e57-Scan-Extractor.git
   cd e57-Scan-Extractor
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the script:

   ```bash
   python e57_scan_extractor.py
   ```

## Usage

1. **Run the Tool**:
   Launch the tool by running `e57_scan_extractor.py`. The GUI window will open.

2. **Select Files**:
   - Click the "Select Files" button to choose `.e57` files for processing.
   - Selected files will be displayed in the GUI.

3. **Set Parameters**:
   - **Bounds Radius (meters)**: Specify the bounding radius for cropping points.
   - **Spacing (meters)**: Set the minimum spacing between points during thinning.

4. **Start Processing**:
   - Click "Start Processing" to begin processing the selected files.
   - A progress bar will indicate the current processing status.
   - Processed files will be saved in an `output` folder in the same directory as the input files.

5. **Output**:
   - Processed `.laz` files and a `coords.csv` file (containing scan metadata) will be generated in the `output` folder.

## File Output

- **LAZ Files**: One `.laz` file per scan, named as `<e57_filename>-<scan_name>.laz`.
- **Metadata File**: `coords.csv` containing the following fields:
  - Origin name
  - Scan name
  - File path
  - Creation date
  - Translation and rotation parameters
  - Scale and offset values

## GUI Overview

- **File Selection**: Button to select `.e57` files for processing.
- **Parameter Inputs**: Input fields for bounds radius and spacing.
- **Progress Bar**: Displays the processing progress.
- **Start Button**: Begins processing the selected files.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please fork the repository, make your changes, and submit a pull request.

## Support

If you encounter issues or have suggestions, feel free to open an issue on the [GitHub Issues](https://github.com/MundaneSoftware/e57-Scan-Extractor/issues) page.

## Acknowledgments

Special thanks to the authors of the following libraries:

- [`pye57`](https://pypi.org/project/pye57/)
- [`laspy`](https://pypi.org/project/laspy/)
- [`scipy`](https://pypi.org/project/scipy/)

---

Happy scanning! 🎉

