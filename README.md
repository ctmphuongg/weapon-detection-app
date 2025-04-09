# Threat Detection System

With school shootings on the rise, our client Critical Reach, a Silicon Valley non-profit, was looking to create a solution to reduce potential threats on school campuses by leveraging AI image recognition technology. This Threat Detection System has the capacity to save lives and is comprised of three components: a threat detection model, a UI, and a data curation tool. The threat detection model identifies five classes of objects: guns, rifles, lenses, wallets, and knives. The threat detection model also features the ability to distinguish people as a police officer or a non-police officer. The UI is simplistic in design as it displays the live camera feed that it is connected to, alerts when a weapon is detected, and the confidence level the algorithm has about the object detected. The data curation tool takes in a video file, slices the file into images, and outputs the images files into a folder.

## Install and Deploy

To get the project up and running on your local machine for development and testing purposes as well as how to deploy the project on a live system, please view the following documents for further instructions:

 - Threat Detection Model: https://gitlab.bucknell.edu/kbw011/senior-design-aiecode/-/blob/8bf97f0e91e571d9e5efc52b806fcb94f6c0673c/models/README.md
 - UI: https://gitlab.bucknell.edu/kbw011/senior-design-aiecode/-/blob/main/UI/README.md?ref_type=heads
 - Data Curation Tool: https://gitlab.bucknell.edu/kbw011/senior-design-aiecode/-/blob/main/data_curation_tool/READ.md?ref_type=heads

## Authors

The following people listed are the authors of this project:
 - Katrina Wilson, Product Owner
 - Connor Coles, Scrum Master
 - Ashley Albert, Developer
 - Derek Araki-Kurdyla, Developer
 - Phuong Cao, Developer
 - Sam Vickers, Developer

## Acknowledgement

This project makes use of the following external resources:
 - TensorFlow (Apache 2.0 License) - tensorflow.org
 - YOLO (AGPL-3.0 License) - ultralytics.com/yolo
 - React (Creative Commons Attribution 4.0 International) - react.dev
 - Fast API (MIT License) - fastapi.tiangolo.com
 - PyTorch (3-Clause BSD License) - pytorch.org
 - Python (PSF License Version 2) - python.org

## License

This project is licensed under the Creative Commons Attribution 4.0 (CC BY-NC-ND) License. Please visit https://creativecommons.org/ for more details.
