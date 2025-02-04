# WarcodesBattleSim
Battle Simulator for the mobile game "Warcodes"
saved_creatures.json included with some basic monsters. Place the file in the same directory as the script.
If you want the monster images to appear, save an image with the same name as a monster in a folder called "Monster Images" in the same directory.

## Build Command
To build the project into a single executable, run:
```
pyinstaller --name warcodes --add-data "Monster Images;Monster Images" --add-data "saved_creatures.json;." --hidden-import PIL --hidden-import PIL._imagingtk --hidden-import PIL._tkinter_finder --onefile warcodes.py
```
