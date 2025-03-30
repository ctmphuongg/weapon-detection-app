import os
import cv2
import torch
import glob
import numpy as np
from ultralytics import YOLO
import hashlib
import sys

# Load your model on CPU. Adjust "best.pt" path if needed.
model = YOLO("best.pt")

def annotate_image(image, valid_classes=None, conf_threshold=0.55, draw_boxes=True):
    """
    Run detection on an image. If a valid detection is found:
      - If draw_boxes is True, draw bounding boxes & labels on the image
      - Otherwise, leave the image unannotated
    Return a list with either [image] if detection found, or [] if no detection.

    :param image: A file path or a NumPy array.
    :param valid_classes: List of valid classes (e.g. ["pistol", "gun"])
    :param conf_threshold: Float confidence threshold.
    :param draw_boxes: Boolean to indicate if bounding boxes/labels should be drawn.
    :return: [annotated_image] if detection found, else [].
    """
    if valid_classes is None:
        valid_classes = ["pistol", "gun"]

    # Load image if a file path is provided
    if isinstance(image, str):
        image = cv2.imread(image)
        if image is None:
            print(f"Error: Could not load image from path: {image}")
            return []

    # Run inference
    results = model(image)

    detection_found = False
    annotated_image = image.copy() if draw_boxes else image  # if we won't draw, no need to copy

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            conf = float(box.conf.cpu().numpy()[0])
            cls = int(box.cls.cpu().numpy()[0])
            detected_class = model.names.get(cls, "")

            if conf >= conf_threshold and detected_class in valid_classes:
                detection_found = True

                if draw_boxes:
                    # Get bounding box coords
                    xyxy = box.xyxy.cpu().numpy()[0]
                    x1, y1, x2, y2 = xyxy.astype(int)

                    # Draw bounding box
                    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Draw label
                    label = f"{detected_class} {conf:.2f}"
                    cv2.putText(
                        annotated_image, label,
                        (x1, max(y1 - 10, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 2
                    )

                # Because your original logic returns the full image on the first valid detection,
                # we can break here if we only need 1 detection to keep the image.
                break

        if detection_found:
            break

    if detection_found:
        return [annotated_image]
    return []

def process_video(video_path, save_folder, valid_classes=None, frame_interval=10, draw_boxes=True):
    """
    Process a single video file, saving frames (with or without bounding boxes)
    if they contain at least one valid detection.
    
    :param video_path: Path to the video file
    :param save_folder: Where detection images will be saved
    :param valid_classes: Which classes to detect
    :param frame_interval: Only save every nth frame
    :param draw_boxes: Boolean to toggle bounding boxes
    """
    if valid_classes is None:
        valid_classes = ["pistol", "gun"]

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process every nth frame
        if frame_count % frame_interval == 0:
            annotated_images = annotate_image(
                frame,
                valid_classes=valid_classes,
                conf_threshold=0.55,
                draw_boxes=draw_boxes
            )
            for i, img in enumerate(annotated_images):
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                out_path = os.path.join(save_folder, f"{video_name}_frame{frame_count}_detection{i}.jpg")
                cv2.imwrite(out_path, img)
                saved_count += 1

        frame_count += 1

    cap.release()
    print(f"Processed '{video_path}': saved {saved_count} detections.")

def process_videos_in_folder(videos_folder, output_folder, valid_classes=None,
                             frame_interval=10, draw_boxes=True):
    """
    Process all videos in a folder, saving detection frames to output_folder.

    :param videos_folder: Folder containing video files
    :param output_folder: Folder where detection frames are saved
    :param valid_classes: Which classes to detect
    :param frame_interval: Save every nth frame
    :param draw_boxes: Boolean to toggle bounding boxes
    """
    if valid_classes is None:
        valid_classes = ["pistol", "gun"]

    # Normalize/abs paths
    videos_folder = os.path.abspath(os.path.normpath(videos_folder))
    output_folder = os.path.abspath(os.path.normpath(output_folder))

    # We only match these four extensions, case-insensitive
    valid_exts = {'.mp4', '.avi', '.mov', '.mkv'}

    # Gather top-level items
    all_items = os.listdir(videos_folder)
    #print("DEBUG: Found these top-level items in folder:", all_items)

    video_files = []
    for item in all_items:
        item_path = os.path.join(videos_folder, item)
        # Check if it's a file (not a folder)
        if os.path.isfile(item_path):
            # Check extension in a case-insensitive way
            ext = os.path.splitext(item)[1].lower()
            if ext in valid_exts:
                video_files.append(item_path)

    if not video_files:
        print(f"No video files found in '{videos_folder}'.")
        return

    #print("DEBUG: Final list of recognized video files:", video_files)

    for video_file in video_files:
        process_video(video_file, output_folder, valid_classes, frame_interval, draw_boxes)

def filter_images(folder, valid_classes=None, conf_threshold=0.55):
    """
    Go through each .jpg image in 'folder'. Delete if it has no valid detections.

    :param folder: Folder of images
    :param valid_classes: Classes to keep (if not found, image is deleted)
    :param conf_threshold: Confidence threshold to consider a detection valid
    """

    folder = os.path.abspath(os.path.normpath(folder))
    
    if valid_classes is None:
        valid_classes = ["pistol", "gun"]

    image_paths = glob.glob(os.path.join(folder, "*.jpg"))
    for image_path in image_paths:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load {image_path}. Skipping...")
            continue

        results = model(image)
        detection_found = False

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                conf = float(box.conf.cpu().numpy()[0])
                cls = int(box.cls.cpu().numpy()[0])
                if conf >= conf_threshold and model.names.get(cls, "") in valid_classes:
                    detection_found = True
                    break
            if detection_found:
                break

        if not detection_found:
            os.remove(image_path)
            print(f"Deleted {image_path} (no valid detection).")
        else:
            print(f"Retained {image_path} (valid detection found).")

def remove_duplicate_images(folder):
    """
    Compute an MD5 hash for each .jpg image in 'folder' and delete duplicates.
    """
    folder = os.path.abspath(os.path.normpath(folder))

    hash_dict = {}
    image_paths = glob.glob(os.path.join(folder, "*.jpg"))
    for path in image_paths:
        with open(path, "rb") as f:
            filehash = hashlib.md5(f.read()).hexdigest()
        if filehash in hash_dict:
            os.remove(path)
            print(f"Deleted duplicate: {path}")
        else:
            hash_dict[filehash] = path

if __name__ == '__main__':
    """
    Usage:
      python videoToImage.py <mode> <draw_boxes> <input_folder> <output_folder> <class1> [class2 ...] <frame_interval> <confidence_level>
    
      Examples:
      1) Process videos with bounding boxes, searching for "pistol" or "gun":
         python videoToImage.py videoShots True /path/to/videos /path/to/output pistol gun 10 0.55
      
      2) Filter images in a folder (no bounding boxes, just deletion):
         python videoToImage.py filterImages False /path/to/images /unused pistol 10 0.55
         # In this example, output_folder is not used, so pass anything ("/unused").
    """

    if len(sys.argv) < 6:
        print("Usage: videoToImage.py <mode> <draw_boxes> <input_folder> <output_folder> <class1> [class2 ...] <frame_interval> <confidence_level>")
        sys.exit(1)

    mode = sys.argv[1]         # "videoShots" or "filterImages"
    draw_boxes_arg = sys.argv[2].lower()  # "true" or "false"
    input_folder = sys.argv[3]
    output_folder = sys.argv[4]

    # Everything from sys.argv[5:-2] are class names
    classes = sys.argv[5:-2]

    # Final args are frame_interval and confidence_level
    try:
        frame_interval = int(sys.argv[-2])
        confidence_level = float(sys.argv[-1])
    except ValueError:
        frame_interval = 10
        confidence_level = 0.55

    # Convert bounding-box arg to boolean
    if draw_boxes_arg in ["true", "1", "yes"]:
        draw_boxes = True
    else:
        draw_boxes = False

    # If no classes specified, default:
    if not classes:
        valid_classes = ["pistol", "gun"]
    else:
        valid_classes = classes

    print(f"Mode: {mode}")
    print(f"Draw boxes: {draw_boxes}")
    print(f"Input folder: {input_folder}")
    if mode == "videoShots":
        print(f"Output folder: {output_folder}")
    else:
        print("Output folder: Not applicable for filterImages mode")
    print(f"Classes: {valid_classes}")
    print(f"Frame interval: {frame_interval}")
    print(f"Confidence level: {confidence_level}")

    if mode == "videoShots":
        process_videos_in_folder(
            input_folder,
            output_folder,
            valid_classes=valid_classes,
            frame_interval=frame_interval,
            draw_boxes=draw_boxes
        )
        print("Finished processing videos into screenshots.")

    elif mode == "filterImages":
        filter_images(
            folder=input_folder,
            valid_classes=valid_classes,
            conf_threshold=confidence_level
        )
        print("Finished filtering images.")

    else:
        print(f"Unknown mode '{mode}'! Use 'videoShots' or 'filterImages'.")
        sys.exit(1)

    print("Done.")
    sys.exit(0)
