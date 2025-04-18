
# Threat Detection Models

This folder contains the trained AI models used in the Threat Detection System:

- Weapon Detection Model
    
    Currently detects five object classes: guns, knives, phones, wallets, and camera lenses.

- Police Identification Model
        
    Determines whether a detected person is a police officer or civilian based on uniform and appearance.

Both models are trained using YOLO and optimized for real-time performance in surveillance environments.

## Usage

Download the desired .pt file and use it wherever you would like. For example, to use the model in the data curation tool you would register the path for it like so: 
```
model = YOLO("____.pt").
```

## Training / Finetuning
In order to train a new model from scratch, from YOLO pretrained weights, or fine tune one of our models, follow these general steps:
1. Prepare the datset

    Ensure your dataset is in YOLO format:
    ```
    .
    └── dataset/
        ├── train/
        │   ├── images
        │   └── labels
        ├── valid/
        │   ├── images
        │   └── labels
        └── test/
            ├── images
            └── labels
    ```
2. Create a data.yaml file specifying class names and paths to `train/`, `valid/`, and `test/` image folders within your dataset.
    
    For example:

    ```
    train: dataset/train/images
    val: dataset/valid/images
    test: dataset/test/images

    nc: 5
    names: ['knife', 'lens', 'monedero', 'pistol', 'smartphone']
    ```

    The paths shown above are relative to dataset_dir in `settings.json`, which can be found like so (assuming ultralytics is installed):
    ```
    $ yolo settings
    ```
3. Train the model

    Python example:
    ```
    from ultralytics import YOLO

    model = YOLO("yolov12m.pt") # Choose any model (can be one of ours)
    model.train(data="path/to/data.yaml", epochs=100, imgsz=640)
    ```

    To train a model from scratch (no pre-existing weights), insert the argument `pretrained=False` into the `model.train()` call.
