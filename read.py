#!/usr/bin/python3

import hashlib, sys, os, zipfile
from nturl2path import pathname2url
from tkinter import *
from tkinter import ttk
from tkinterweb import HtmlFrame
import sv_ttk
import xml.etree.ElementTree as ET

class Read:
    def __init__(self, root):
        self.history = [0] # Stack maintaining the navigation history of the chapters

        self.custom_css = """ 
            body {
                font-family: 'Open Sans', sans-serif;
                line-height: 1.75em;
                font-size: 16px;
                background-color: #222;
                color: #aaa;
            }

            p {
                font-size: 16px;
            }

            h1 {
                font-size: 30px;
                line-height: 34px;
            }

            h2 {
                font-size: 20px;
                line-height: 25px;
            }

            h3 {
                font-size: 16px;
                line-height: 27px;
                padding-top: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid #D8D8D8;
                border-top: 1px solid #D8D8D8;
            }

            hr {
                height: 1px;
                background-color: #d8d8d8;
                border: none;
                width: 100%;
                margin: 0px;
            }

            a[href] {
                color: #1e8ad6;
            }

            a[href]:hover {
                color: #3ba0e6;
            }

            img {
                max-width: 100%;
            }

            li {
                line-height: 1.5em;
            }
        """
        
        self.appdata_dir = (os.path.join(os.getenv("APPDATA"), "read.py"))
        try: # first ever launch: create appdata dir
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

        self.container_el = ET.parse(os.path.join(self.cache_path, 'META-INF', 'container.xml'))

        # Find .opf file describing the structure of the epub.
        for el in self.container_el.findall('.//*[@media-type]'):
            if el.attrib['media-type'] == 'application/oebps-package+xml':
                self.full_path = el.attrib['full-path']
                self.index_dir = os.path.join(self.cache_path, *self.full_path.split("/")[:-1])
                self.index_path = os.path.join(self.cache_path, *self.full_path.split("/"))

        if not self.index_path:
            print("Cannot find path to OPF file in container.xml.")
            exit(1)
            
        # Find manifest and spine
        self.content_opf = ET.parse(self.index_path).getroot()
        self.manifest_el = self.content_opf.find(f".//{{{self.namespace(self.content_opf)}}}manifest")
        self.spine_el = self.content_opf.find(f".//{{{self.namespace(self.content_opf)}}}spine")

        self.spine = [x.attrib['idref'] for x in self.spine_el] # List of idrefs giving the book contents
        self.book_title = self.find_unique(".//{http://purl.org/dc/elements/1.1/}title", self.content_opf).text

        root.title(self.book_title)

        self.mainframe = ttk.Frame(root, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.html_frame = HtmlFrame(self.mainframe, vertical_scrollbar="true", messages_enabled=False)
        self.html_frame.grid(column=1, row=1)
        
        # Set up callbacks
        self.html_frame.on_url_change(self.update_current_item)
        self.html_frame.on_done_loading(lambda: self.html_frame.add_css(self.custom_css))

        ttk.Button(self.mainframe, text="Prev", command=self.load_prev).grid(column=1, row=2, sticky=W)
        ttk.Button(self.mainframe, text="Next", command=self.load_next).grid(column=1, row=2)
        ttk.Button(self.mainframe, text="Back", command=self.go_back).grid(column=1, row=2, sticky=E)
        root.bind("<Left>", lambda _: self.load_prev())
        root.bind("<Right>", lambda _: self.load_next())

        self.load_current_item()

    def print_parsed_metadata(self): # Debug
        print("book:", self.book_title)
        print("spine:", self.spine)
        print("manifest.xml:", self.manifest_el)
        print("content.opf:", self.content_opf)

    def namespace(self, el):
        return el.tag.split('}')[0].strip('{')
                
    def find_unique(self, tag, el):
        matching_items = el.findall(tag)
        if len(matching_items) != 1:
            print(f"Cannot find manifest item for idref {self.idref}!")
            exit(1)
        return matching_items[0]
        
    def child_with_id(self, id, el):
        matching_items = el.findall(f".//*[@id='{id}']")
        if len(matching_items) != 1:
            print(f"Cannot find manifest item for idref {self.idref}!")
            exit(1)
        return matching_items[0]
        
    # Get the path to a spine item given by index
    def get_path(self, item):
        idref = self.spine[item]
        href = self.child_with_id(idref, self.manifest_el).attrib['href']
        return pathname2url(os.path.join(self.index_dir, *href.split("/")))
        
    # Inverse of get_path: get spine index given path
    # may return None, which just means the currently opened page won't be added to history 
    # this happens e.g. if we end up on a webpage
    def get_index(self, path):
        for child in self.manifest_el:
            if path in child.attrib['href']:
                try:
                    return self.spine.index(child.attrib['id'])
                except ValueError: 
                    pass    
        
    def load_prev(self):
        if self.current_index() > 0:
            self.history.append(self.current_index() - 1)
        self.load_current_item()

    def load_next(self):
        if self.current_index() < len(self.spine) - 1:
            self.history.append(self.current_index() + 1)
        self.load_current_item()
        
    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            self.load_current_item()
        
    # Load contents of current chapter into HTML frame.
    def load_current_item(self):
        self.html_frame.add_css(self.custom_css)
        self.html_frame.load_file(self.get_path(self.current_index()))
        
    # Callback when a link is clicked.
    def update_current_item(self, url):
        index = self.get_index(os.path.basename(url))
        if self.current_index() != index and index != None:
            self.history.append(index)
            
    def current_index(self):
        return self.history[-1]
                

if __name__ == "__main__":
    root = Tk()

    sv_ttk.use_dark_theme() # Sun Valley dark theme.

    Read(root)
    
    #####################
    # FIXES FOR WINDOWS #
    #####################

    import ctypes

    # Fix blurry scaling for HiDPI on Windows
    ctypes.windll.shcore.SetProcessDpiAwareness(1) 

    # Make the title bar dark, cp. https://gist.github.com/Olikonsti/879edbf69b801d8519bf25e804cec0aa
    root.update()
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    value = ctypes.c_int(2) # Pass 0 here for a white title bar.
    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
    # On Win10, above code only works once the window has been resized, so change it and reset it...
    root.geometry(str(root.winfo_width()+1) + "x" + str(root.winfo_height()+1))
    root.geometry(str(root.winfo_width()-1) + "x" + str(root.winfo_height()-1))

    #########################
    # END FIXES FOR WINDOWS #
    #########################

    root.mainloop()
