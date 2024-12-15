import asyncio
import os
import gc
import io

import numpy as np
from pathlib import Path
from pye57 import E57
from datetime import datetime
import laspy
from scipy.spatial import cKDTree

from tkinter import Tk, Label, Button, filedialog, StringVar, Entry, messagebox
from tkinter.ttk import Progressbar

def create_directory_if_not_exist(directory_path):
    """
    Ensures a directory exists, creating it if necessary.

    Args:
        directory_path (Path): Directory path to check/create.
    """
    dir_path = Path(directory_path)
    if not dir_path.exists():
        print(f"Creating directory: {directory_path}")
        dir_path.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Directory already exists: {directory_path}")

def select_files():
    """
    Opens a dialog to select multiple E57 files and updates the file paths in the GUI.
    """
    paths = filedialog.askopenfilenames(
        title="Select E57 Files",
        filetypes=[("E57 files", "*.e57"), ("All files", "*.*")]
    )
    if paths:
        selected_paths.set(paths)
        input_path.set(f"{len(paths)} file(s) selected")
    else:
        input_path.set("No files selected")

def start_processing():
    """
    Validates user input and starts the async processing of selected E57 files.
    """
    paths_str = selected_paths.get()
    if not paths_str:
        messagebox.showerror("Error", "No files selected for processing!")
        return

    # Validate and parse the user inputs for bounds and spacing
    try:
        bounds_radius = float(bounds_radius_var.get())
        spacing = float(spacing_var.get())
        if bounds_radius <= 0 or spacing <= 0:
            raise ValueError("Bounds radius and spacing must be positive numbers.")
    except ValueError as e:
        messagebox.showerror("Error", f"Invalid input: {e}")
        return

    try:
        paths_str = paths_str.strip("[]")
        paths_list = [path.strip(" '").strip("('").strip("')") for path in paths_str.split(",")]
    except Exception as e:
        messagebox.showerror("Error", f"Failed to parse file paths: {e}")
        return

    # Replace the label with a progress bar during processing
    entry.pack_forget()
    progress_bar.pack(pady=10)

    # Run the processing with the user-defined bounds and spacing
    asyncio.run(extract_scans(paths_list, progress_bar, bounds_radius, spacing))

    # Reset the UI after processing
    progress_bar.pack_forget()
    entry.pack(pady=10)
    messagebox.showinfo("Success", "Processing complete!")

async def extract_scans(file_paths, progress_bar, bounds_radius, spacing):
    """
    Extracts scans from E57 files, applying bounds and spacing filters, and saves them as LAZ files.

    Args:
        file_paths (list): List of file paths to process.
        progress_bar (Progressbar): Progress bar to update.
        bounds_radius (float): Bounding radius for cropping points.
        spacing (float): Minimum spacing between points during thinning.
    """
    if not file_paths:
        print("No files selected.")
        return

    # Define the output directory
    output_path = Path(file_paths[0]).parent / "output"
    create_directory_if_not_exist(output_path)

    # Ensure the coords file exists
    coords_file_path = Path(output_path) / "coords.csv"
    if not coords_file_path.exists():
        print(f"Creating coords file: {coords_file_path}")
        with open(coords_file_path, 'w') as f:
            f.write("origin_name,scan_name,scan_path,creation_date,translation_x,translation_y,translation_z," +
                    "rotation_x,rotation_y,rotation_z,rotation_w,scale_x,scale_y,scale_z,offset_x,offset_y,offset_z\n")

    # Initialize progress tracking
    current_progress = [0]
    progress_bar["maximum"] = len(file_paths)

    # Process each file
    for file_path in file_paths:
        if not file_path.endswith('.e57'):
            print(f"Skipping non-E57 file: {file_path}")
            continue
        await process_e57_file(file_path, output_path, coords_file_path, progress_bar, current_progress, bounds_radius, spacing)

async def process_e57_file(file_path, output_path, coords_file_path, progress_bar, current_progress, bounds_radius, spacing):
    """
    Processes an individual E57 file and extracts scans as LAZ files.

    Args:
        file_path (str): Path to the E57 file.
        output_path (Path): Directory to save output files.
        coords_file_path (Path): Path to the coordinates CSV file.
        progress_bar (Progressbar): Progress bar to update.
        current_progress (list): List to track progress.
        bounds_radius (float): Bounding radius for cropping points.
        spacing (float): Minimum spacing between points during thinning.
    """
    # Ensure the file exists before processing
    if not os.path.exists(file_path):
        print(f"E57 file not found at path: {file_path}")
        raise FileNotFoundError(f"E57 file not found at path: {file_path}")

    e57_file = E57(str(file_path))
    e57_file_name = os.path.splitext(os.path.basename(file_path))[0]
    num_scans = e57_file.scan_count
    imf = e57_file.image_file
    root = imf.root()
    creation_datetime = datetime.fromtimestamp(root['creationDateTime']["dateTimeValue"].value())
    formatted_datetime = creation_datetime.strftime("%Y-%m-%d %H:%M:%S")

    for scan_index in range(num_scans):
        # Extract point cloud
        scan_header = e57_file.get_header(scan_index)
        translation = scan_header.translation
        rotation = scan_header.rotation
        guid = scan_header['guid'].value()
        name = scan_header['name'].value()

        bounds = {
            'maxX': float(translation[0]) + bounds_radius,
            'maxY': float(translation[1]) + bounds_radius,
            'maxZ': float(translation[2]) + bounds_radius,
            'minX': float(translation[0]) - bounds_radius,
            'minY': float(translation[1]) - bounds_radius,
            'minZ': float(translation[2]) - bounds_radius
        }

        scales = (
            scan_header['cartesianXScaling'].value() if 'cartesianXScaling' in scan_header else 0.001,
            scan_header['cartesianYScaling'].value() if 'cartesianYScaling' in scan_header else 0.001,
            scan_header['cartesianZScaling'].value() if 'cartesianZScaling' in scan_header else 0.001
        )

        offsets = (
            scan_header['cartesianXOffset'].value() if 'cartesianXOffset' in scan_header else 0.0,
            scan_header['cartesianYOffset'].value() if 'cartesianYOffset' in scan_header else 0.0,
            scan_header['cartesianZOffset'].value() if 'cartesianZOffset' in scan_header else 0.0
        )

        # Create LAS header
        header = laspy.LasHeader(point_format=3, version="1.4")
        header.scales = scales
        header.offsets = offsets

        las_file_name = f"{e57_file_name}-{name}.laz"
        las_full_path = Path(output_path) / las_file_name

        scan = e57_file.read_scan(scan_index, intensity=True, colors=True, ignore_missing_fields=True)

        # Open LAS file for writing in batches
        with laspy.open(las_full_path, mode='w', header=header) as writer:
            num_points = len(scan['cartesianX'])
            batch_size = 1000000  # Batch size of 1 million points

            # Process points in batches
            for start_idx in range(0, num_points, batch_size):
                end_idx = min(start_idx + batch_size, num_points)
                print(f"Processing batch: {start_idx} to {end_idx}")

                # Extract the current batch of points
                point_batch = np.vstack((scan['cartesianX'][start_idx:end_idx],
                                         scan['cartesianY'][start_idx:end_idx],
                                         scan['cartesianZ'][start_idx:end_idx])).T

                # Apply cropping filters
                x_filter = (point_batch[:, 0] >= bounds['minX']) & (point_batch[:, 0] <= bounds['maxX'])
                y_filter = (point_batch[:, 1] >= bounds['minY']) & (point_batch[:, 1] <= bounds['maxY'])
                z_filter = (point_batch[:, 2] >= bounds['minZ']) & (point_batch[:, 2] <= bounds['maxZ'])
                valid_points_filter = x_filter & y_filter & z_filter

                if np.any(valid_points_filter):
                    cropped_points = point_batch[valid_points_filter]

                    # Apply thinning logic
                    tree = cKDTree(cropped_points)
                    mask = np.ones(len(cropped_points), dtype=bool)

                    for i, point in enumerate(cropped_points):
                        if mask[i]:
                            indices = tree.query_ball_point(point, spacing)
                            mask[indices[1:]] = False  # Keep only the first point, discard nearby points

                    thinned_points = cropped_points[mask]

                    # Create ScaleAwarePointRecord for the thinned points
                    point_record = laspy.ScaleAwarePointRecord.zeros(len(thinned_points), point_format=header.point_format, scales=header.scales, offsets=header.offsets)

                    # Assign x, y, z values to the record
                    point_record.x = thinned_points[:, 0]
                    point_record.y = thinned_points[:, 1]
                    point_record.z = thinned_points[:, 2]

                    # Handle optional attributes like intensity and color if they exist
                    if 'intensity' in scan:
                        point_record.intensity = scan['intensity'][start_idx:end_idx][valid_points_filter][mask].astype(np.uint16)

                    if 'colorRed' in scan:
                        point_record.red = scan['colorRed'][start_idx:end_idx][valid_points_filter][mask].astype(np.uint16)
                        point_record.green = scan['colorGreen'][start_idx:end_idx][valid_points_filter][mask].astype(np.uint16)
                        point_record.blue = scan['colorBlue'][start_idx:end_idx][valid_points_filter][mask].astype(np.uint16)

                    # Write the thinned points to the LAZ file
                    writer.write_points(point_record)

                # Free memory by deleting batch-specific variables and forcing garbage collection
                del point_batch, valid_points_filter, cropped_points, thinned_points, point_record
                gc.collect()

        with open(coords_file_path, 'a') as f:
            f.write(f"{e57_file_name},{las_file_name},{las_full_path},{formatted_datetime},{translation[0]},{translation[1]},{translation[2]},"
                    f"{rotation[1]},{rotation[2]},{rotation[3]},{rotation[0]},{scales[0]},{scales[1]},{scales[2]},{offsets[0]},{offsets[1]},{offsets[2]}\n")

    e57_file.close()

    # Update the progress bar after processing each file
    current_progress[0] += 1
    progress_bar["value"] = current_progress[0]
    progress_bar.update_idletasks()

# GUI Setup
root = Tk()
root.title("E57 Scan Extractor")

input_path = StringVar()
selected_paths = StringVar()
bounds_radius_var = StringVar(value="10")  # Default value for bounds radius
spacing_var = StringVar(value="0.005")    # Default value for spacing

# GUI Components
Label(root, text="Select E57 files:").pack(pady=10)
entry = Label(root, textvariable=input_path, width=50, relief="sunken", anchor="w")
entry.pack(pady=5)

Label(root, text="Bounds Radius (meters):").pack(pady=5)
bounds_radius_entry = Entry(root, textvariable=bounds_radius_var, width=20)
bounds_radius_entry.pack(pady=5)

Label(root, text="Spacing (meters):").pack(pady=5)
spacing_entry = Entry(root, textvariable=spacing_var, width=20)
spacing_entry.pack(pady=5)

progress_bar = Progressbar(root, orient="horizontal", mode="determinate", length=300)

Button(root, text="Select Files", command=select_files).pack(pady=5)
Button(root, text="Start Processing", command=start_processing).pack(pady=10)

# Start the GUI
root.geometry("400x300")
root.mainloop()
