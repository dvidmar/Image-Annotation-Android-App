# Image-Annotation-Android-App

A Kivy app to annotate either bounding boxes or painted boundaries over a folder of images.

![alt text](/json/bb_annotation.png) ![alt text](/json/paint_annotation.png)

The app starts in bounding box mode, where a double tap will create a bounding box and finger squeeze will resize the box.  Tap on toggle paint to restart your annotation in paint mode, where you can draw free-form boundaries around objects.  Each stroke will be saved as a separate object.  Tapping submit annotation will save the current annotation and take you to the next image in the folder.

To push the main app to your android device, follow the Kivy instructions here: https://github.com/kivy/kivy.  Your annotations are saved in a JSON file as you go, and resumed every time you open the app.  

To gather and plot your annotations in python, transfer the saved JSON file to your computer and follow the notebooks in the json folder.
