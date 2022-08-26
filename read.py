#!/usr/bin/python3

import hashlib
import sys, os, zipfile
import tkinter as tk
from tkinterweb import HtmlFrame
import xml.etree.ElementTree as ET

from ctypes import windll
windll.shcore.SetProcessDpiAwareness(1) # Fix blurry scaling for HiDPI on Windows

def namespace(el):
    return el.tag.split('}')[0].strip('{')
            
appdata_dir = (os.path.join(os.getenv("APPDATA"), "read.py"))
try:
    os.mkdir(appdata_dir)
except FileExistsError:
    pass

# extract epub contents to appdata directory, unless already present.
with open(sys.argv[1], "rb") as file:
    book_hash = hashlib.md5(file.read()).hexdigest() # use md5 as ID
    try:
        cache_path = os.path.join(appdata_dir, book_hash)
        os.mkdir(cache_path)
        with zipfile.ZipFile(sys.argv[1]) as epub:
            epub.extractall(cache_path)
    except FileExistsError:  # work already done
        pass

with zipfile.ZipFile(sys.argv[1]) as epub:
    namelist = epub.namelist()
    files = {name: epub.read(name) for name in namelist} # Unzip into memory
    root = ET.fromstring(files['META-INF/container.xml'])

# Find .opf file describing the structure of the epub.
for el in root.findall('.//*[@media-type]'):
    if el.attrib['media-type'] == 'application/oebps-package+xml':
        index_path = el.attrib['full-path']

if not index_path:
    print("Cannot find path to OPF file in container.xml.")
    exit(1)
    
# Find manifest and spine
root = ET.fromstring(files[index_path])
manifest_el = root.find(f".//{{{namespace(root)}}}manifest")
spine_el = root.find(f".//{{{namespace(root)}}}spine")
spine = [x.attrib['idref'] for x in spine_el]

# Get the path for a manifest item identified via idref.
def get_path(idref, manifest):
    matching_items = manifest.findall(f".//*[@id='{idref}']")
    if len(matching_items) != 1:
        print(f"Cannot find manifest item for idref {idref}!")
        exit(1)

    # turn href into absolute path
    return os.path.dirname(index_path) + "/" + matching_items[0].attrib['href']

# Get the (X)HTML for a spine item.
def get_html(index):
    return files[get_path(spine[index], manifest_el)].decode()
    
root = tk.Tk()
frame = HtmlFrame(root, horizontal_scrollbar="auto")
frame.on_downloading_resource(print)

frame.load_html(get_html(4))
frame.pack(fill="both", expand=True) #attach the HtmlFrame widget to the parent window
#with open("ch13.html", encoding='utf-8') as f:
#    frame.load_html(f.read())

root.mainloop()

# TODO. For loading files, which we unzip into memory. Change utilities.py line ~580
# download method. The files dict should simply shadow urlopen(). 
# * Need to figure out how to tell when a local file is referred.
#   * Lib provides on_downloading_Resource callback, and os.path.relpath can be used to get rid of ../ in the path
# * Needs the content type for each file, which is given in the opf! So just parse that as well.
