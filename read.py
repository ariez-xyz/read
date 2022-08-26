#!/usr/bin/python3

import hashlib, sys, os, zipfile
from nturl2path import pathname2url
import tkinter as tk
from tkinter import ttk
from tkinterweb import HtmlFrame
import xml.etree.ElementTree as ET

from ctypes import windll
windll.shcore.SetProcessDpiAwareness(1) # Fix blurry scaling for HiDPI on Windows

def namespace(el):
    return el.tag.split('}')[0].strip('{')
            
def child_with_id(id, el):
    matching_items = el.findall(f".//*[@id='{id}']")
    if len(matching_items) != 1:
        print(f"Cannot find manifest item for idref {idref}!")
        exit(1)
    return matching_items[0]
    
# Get the path to a spine item
def get_path(idref, manifest):
    href = child_with_id(idref, manifest).attrib['href']
    return pathname2url(os.path.join(index_dir, *href.split("/")))
    
            
appdata_dir = (os.path.join(os.getenv("APPDATA"), "read.py"))
try: # first launch
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

root = ET.parse(os.path.join(cache_path, 'META-INF', 'container.xml'))

# Find .opf file describing the structure of the epub.
for el in root.findall('.//*[@media-type]'):
    if el.attrib['media-type'] == 'application/oebps-package+xml':
        full_path = el.attrib['full-path']
        index_dir = os.path.join(cache_path, *full_path.split("/")[:-1])
        index_path = os.path.join(cache_path, *full_path.split("/"))

if not index_path:
    print("Cannot find path to OPF file in container.xml.")
    exit(1)
    
# Find manifest and spine
root = ET.parse(index_path).getroot()
manifest_el = root.find(f".//{{{namespace(root)}}}manifest")
spine_el = root.find(f".//{{{namespace(root)}}}spine")

spine = [x.attrib['idref'] for x in spine_el] # List of idrefs giving the book contents
book_title = child_with_id('title', root).text #

root = tk.Tk()
root.title(book_title)
frame = HtmlFrame(root, horizontal_scrollbar="auto", messages_enabled=False)

frame.load_file(get_path(spine[4], manifest_el))
frame.pack(fill="both", expand=True) #attach the HtmlFrame widget to the parent window
#with open("ch13.html", encoding='utf-8') as f:
#    frame.load_html(f.read())

root.mainloop()
