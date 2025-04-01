# Video-to-Image Electron App

A simple Electron-based UI for processing videos or images with a Python script (`videoToImage.py`). Users can:

- **Pick a folder** containing videos to extract frames from (based on object detection).
- **Pick a folder** containing images to filter (removing those without valid detections).
- **Toggle bounding boxes** on the saved frames.
- **Cancel** an ongoing Python process if you run the wrong script by accident.

---

## Prerequisites

Before you continue, ensure you have met the following requirements:

- **Node.js** (v14 or newer)
- **npm** or **yarn**
- **Electron** (installed as a `devDependency` in this repo)
- **Python** (3.8+ recommended)
- **Python libraries**:
   - `ultralytics`
   - `torch`
   - `opencv-python`
   - (and any others needed by your YOLO model)

---

## Installation

1. Clone or download this repository.
2. In the project folder, run:
    ```bash
    npm install
    ```

---

## Usage

1. Start the Electron app with:
    ```bash
    npm start
    ```

2. Choose one of the two modes:
    - **Process Videos (videoShots)**: Extract frames from videos where a valid detection is found.
    - **Filter Images (filterImages)**: Remove images with no valid detection.

3. Optionally, specify custom YOLO-detected classes and confidence thresholds.

4. Toggle bounding boxes if needed.

5. Cancel a running process if required.

---

## Features

1. **Two Modes**  
    - **Process Videos**: Extract frames from videos based on object detection.  
    - **Filter Images**: Remove images without valid detections.

2. **Custom Classes**  
    - Specify YOLO-detected classes (e.g., `pistol`, `gun`).
    - Set a confidence threshold (e.g., `0.5` for 50% confidence).

3. **Bounding Boxes**  
    - Optionally draw bounding boxes on extracted frames.

4. **Cancel Running Process**  
    - Cancel a script if it takes too long or was selected by mistake.

---

## Folder Structure

```
my-electron-app/
├── main.js          # Electron main process. Spawns Python.
├── preload.js       # Bridges the main process and renderer.
├── index.html       # Your UI (renderer).
├── videoToImage.py  # Python script for video or image processing.
├── package.json     # Project metadata and dependencies.
└── (optional) styles.css
```

---

## Contributors

- **Sentinel Team**: Development and maintenance.

---

## License


---

## Contact

For questions or collaboration, reach out to the Sentinel Team.
