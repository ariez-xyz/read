#!/usr/bin/python3

import hashlib, sys, os, zipfile
from nturl2path import pathname2url
from tkinter import *
from tkinter import ttk
from tkinterweb import HtmlFrame
import xml.etree.ElementTree as ET

from ctypes import windll
windll.shcore.SetProcessDpiAwareness(1) # Fix blurry scaling for HiDPI on Windows

current_spine_item = 0

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
    
def load_prev():
    global current_spine_item
    if current_spine_item > 0:
        current_spine_item -= 1
    html_frame.load_file(get_path(spine[current_spine_item], manifest_el))

def load_next():
    global current_spine_item
    if current_spine_item < len(spine) - 1:
        current_spine_item += 1
    html_frame.load_file(get_path(spine[current_spine_item], manifest_el))
            
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

root = Tk()
root.title(book_title)

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

html_frame = HtmlFrame(mainframe, horizontal_scrollbar="auto", messages_enabled=False)
html_frame.load_file(get_path(spine[current_spine_item], manifest_el))
html_frame.grid(column=1, row=1)

ttk.Button(mainframe, text="Prev", command=load_prev).grid(column=1, row=2, sticky=W)
ttk.Button(mainframe, text="Next", command=load_next).grid(column=2, row=2, sticky=E)

root.mainloop()
