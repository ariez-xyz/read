#!/usr/bin/python3

import hashlib, sys, os, zipfile
from nturl2path import pathname2url
from tkinter import *
from tkinter import ttk
from tkinterweb import HtmlFrame
import xml.etree.ElementTree as ET

class Read:
    def __init__(self, root):
        self.current_spine_item = 0

        self.appdata_dir = (os.path.join(os.getenv("APPDATA"), "read.py"))
        try: # first launch
            os.mkdir(self.appdata_dir)
        except FileExistsError:
            pass

        # extract epub contents to appdata directory, unless already present.
        with open(sys.argv[1], "rb") as file:
            self.book_hash = hashlib.md5(file.read()).hexdigest() # use md5 as ID
            try:
                self.cache_path = os.path.join(self.appdata_dir, self.book_hash)
                os.mkdir(self.cache_path)
                with zipfile.ZipFile(sys.argv[1]) as epub:
                    epub.extractall(self.cache_path)
            except FileExistsError:  # work already done
                pass

        root_el = ET.parse(os.path.join(self.cache_path, 'META-INF', 'container.xml'))

        # Find .opf file describing the structure of the epub.
        for el in root_el.findall('.//*[@media-type]'):
            if el.attrib['media-type'] == 'application/oebps-package+xml':
                self.full_path = el.attrib['full-path']
                self.index_dir = os.path.join(self.cache_path, *self.full_path.split("/")[:-1])
                self.index_path = os.path.join(self.cache_path, *self.full_path.split("/"))

        if not self.index_path:
            print("Cannot find path to OPF file in container.xml.")
            exit(1)
            
        # Find manifest and spine
        root_el = ET.parse(self.index_path).getroot()
        self.manifest_el = root_el.find(f".//{{{self.namespace(root_el)}}}manifest")
        self.spine_el = root_el.find(f".//{{{self.namespace(root_el)}}}spine")

        self.spine = [x.attrib['idref'] for x in self.spine_el] # List of idrefs giving the book contents
        self.book_title = self.child_with_id('title', root_el).text #

        root.title(self.book_title)

        self.mainframe = ttk.Frame(root, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.html_frame = HtmlFrame(self.mainframe, horizontal_scrollbar="auto", messages_enabled=False)
        self.html_frame.load_file(self.get_path(self.current_spine_item))
        self.html_frame.grid(column=1, row=1)

        ttk.Button(self.mainframe, text="Prev", command=self.load_prev).grid(column=1, row=2, sticky=W)
        ttk.Button(self.mainframe, text="Next", command=self.load_next).grid(column=2, row=2, sticky=E)
        root.bind("<Left>", self.load_prev)
        root.bind("<Right>", self.load_next)


    def namespace(self, el):
        return el.tag.split('}')[0].strip('{')
                
    def child_with_id(self, id, el):
        matching_items = el.findall(f".//*[@id='{id}']")
        if len(matching_items) != 1:
            print(f"Cannot find manifest item for idref {self.idref}!")
            exit(1)
        return matching_items[0]
        
    # Get the path to a spine item
    def get_path(self, item):
        idref = self.spine[item]
        href = self.child_with_id(idref, self.manifest_el).attrib['href']
        return pathname2url(os.path.join(self.index_dir, *href.split("/")))
        
    def load_prev(self, *args):
        if self.current_spine_item > 0:
            self.current_spine_item -= 1
        self.html_frame.load_file(self.get_path(self.current_spine_item))

    def load_next(self, *args):
        if self.current_spine_item < len(self.spine) - 1:
            self.current_spine_item += 1
        self.html_frame.load_file(self.get_path(self.current_spine_item))
                

if __name__ == "__main__":
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1) # Fix blurry scaling for HiDPI on Windows

    root = Tk()
    Read(root)
    root.mainloop()