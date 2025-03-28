# Video-to-Image Electron App
### By the Sentinel Team

A simple Electron-based UI for processing videos or images with a Python script (`videoToImage.py`). Users can:

- **Pick a folder** containing videos to extract frames from (based on object detection).
- **Pick a folder** containing images to filter (removing those without valid detections).
- **Toggle bounding boxes** on the saved frames.
- **Cancel** an ongoing Python process if you run the wrong script by accident.

---

## Features

1. **Two Modes**  
   - **Process Videos (videoShots)**: Pulls frames from videos where a valid detection is found.  
   - **Filter Images (filterImages)**: Removes images with no valid detection.

2. **Custom Classes**  
   - Specify which YOLO-detected classes you care about (e.g., `pistol`, `gun`).

3. **Bounding Boxes**  
   - Optionally draw bounding boxes on extracted frames.

4. **Cancel Running Process**  
   - If the script is taking too long or was selected by mistake, cancel it via a dedicated button.

---

## Requirements

1. **Node.js** (v14 or newer)
2. **npm** or **yarn**
3. **Electron** (installed as a `devDependency` in this repo)
4. **Python** (3.8+ recommended)
5. **Python libraries**:
   - `ultralytics`
   - `torch`
   - `opencv-python`
   - (and any others needed by your YOLO model)

---

## Installation

1. **Clone** or download this repository.
2. In the project folder, run:
   ```bash 
   npm install 

## Start 

1. Start the electron app with
    ```bash 
    npm start

## Folder Structure

    my-electron-app/
    ├── main.js
    ├── preload.js
    ├── index.html
    ├── videoToImage.py
    ├── package.json
    └── (optional) styles.css
main.js: Electron main process. Spawns Python.
preload.js: Bridges the main process and renderer.
index.html: Your UI (renderer).
videoToImage.py: Python script for video or image processing.


