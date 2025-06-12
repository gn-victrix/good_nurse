### Imports
import tkinter as tk # GUI toolkit
from tkinter import filedialog, messagebox, ttk
from zipfile import ZipFile # interact with zip files
import os # interacts with operating system

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD # for drag and drop function
except ImportError:
    messagebox.showerror("tkinterdnd2 not found", "Please install tkinterdnd2 to enable drag and drop.")
    exit(1)


class ZipEditorTab(tk.Frame):
    def __init__(self, master, zip_path):
        super().__init__(master)
        self.zip_path = zip_path
        self.create_widgets()
        self.text_area.tag_config('highlight', background='yellow', foreground='black')  # Configure tag once here
        self.load_zip()

    def create_widgets(self):
        """
        Create widgets for each tab
        """
        control_frame = tk.Frame(self)
        control_frame.pack(padx=5, pady=5)

        self.text_area = tk.Text(self, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def load_zip(self):
        """
        Loads ZIP files
        """
        try:
            with ZipFile(self.zip_path, 'r') as zip_ref:
                txt_files = [f for f in zip_ref.infolist() if f.filename.endswith('.txt') and f.file_size > 0]
                
                if not txt_files:
                    messagebox.showinfo("No .txt Files", f"No .txt files found in {os.path.basename(self.zip_path)}.")
                    return
                ## function which orders the files e.g. device data first OR write them all to one txt file and extract the info like that?
                for file_info in txt_files:
                    with zip_ref.open(file_info.filename) as file:
                        header = f"\n📄 {file_info.filename}\n"
                        self.text_area.insert(tk.END, header)
                        content = file.read().decode('utf-8')
                        self.text_area.insert(tk.END, content)

        except Exception as e:
            messagebox.showerror("Error", str(e))


    def search_text(self):
        """
        Searches through on-screen text
        """
        self.text_area.tag_remove('highlight', '1.0', tk.END)
        query = self.search_entry.get().strip()
        if not query:
            return

        start = '1.0'
        found = False

        while True:
            pos = self.text_area.search(query, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.text_area.tag_add('highlight', pos, end)
            start = end
            found = True

        if not found:
            messagebox.showinfo("No Results", f"No matches found for '{query}'.")

    def clear_search(self):
        """ 
        Clears Search
        """ 
        self.text_area.tag_remove('highlight', '1.0', tk.END)
        self.search_entry.delete(0, tk.END)


### Main Application Window

class ZipApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("GoodDoctor PRO v3")
        self.geometry("1000x700")

        self.closed_tabs = []

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_frame = tk.Frame(self)
        top_frame.pack(pady=5)

        label = tk.Label(top_frame, text="Drop one or more .zip files here or use the File menu")
        label.pack(side=tk.LEFT, padx=5)

        self.restore_last_btn = tk.Button(top_frame, text="Restore Last Closed Tab", command=self.restore_tab)
        self.restore_last_btn.pack(side=tk.LEFT, padx=5)

        self.restore_all_btn = tk.Button(top_frame, text="Restore All Tabs", command=self.restore_all_tabs)
        self.restore_all_btn.pack(side=tk.LEFT, padx=5)

        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)

        self.notebook.bind("<Button-2>", self.middle_click_close)
        self.notebook.bind("<Button-3>", self.right_click_menu)

        self.create_menu()

    def create_menu(self):
        """
        Creates menu at the top where you can upload a ZIP file by selecting it
        """
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open ZIP File", command=self.open_zip_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

    def open_zip_file(self):
        """
        Opens ZIP file when it is selected from downloads
        """
        zip_path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if zip_path:
            self.add_zip_tab(zip_path)


    def on_drop(self, event):
        dropped_files = event.data.split()
        for path in dropped_files:
            path = path.strip('{}')
            if path.lower().endswith(".zip") or path.lower().endswith(".gnd"):
                self.add_zip_tab(path)
            else:
                messagebox.showerror("Invalid File", f"File '{path}' is not a .zip file.")

    def add_zip_tab(self, zip_path):
        tab = ZipEditorTab(self.notebook, zip_path)
        tab_title = os.path.basename(zip_path)
        self.notebook.add(tab, text=tab_title)
        self.notebook.select(tab)

    def close_tab(self, tab_id):
        index = self.notebook.index(tab_id)
        title = self.notebook.tab(tab_id, "text")
        widget = self.notebook.nametowidget(tab_id)
        self.closed_tabs.append((title, widget.zip_path))
        self.notebook.forget(index)

    def restore_tab(self):
        if not self.closed_tabs:
            messagebox.showinfo("Nothing to Restore", "No recently closed tabs.")
            return

        title, zip_path = self.closed_tabs.pop()
        new_tab = ZipEditorTab(self.notebook, zip_path)
        self.notebook.add(new_tab, text=title)
        self.notebook.select(new_tab)

    def restore_all_tabs(self):
        if not self.closed_tabs:
            messagebox.showinfo("Nothing to Restore", "No recently closed tabs.")
            return

        while self.closed_tabs:
            self.restore_tab()

    def middle_click_close(self, event):
        tab_id = self.get_tab_under_mouse(event)
        if tab_id:
            self.close_tab(tab_id)

    def right_click_menu(self, event):
        tab_id = self.get_tab_under_mouse(event)
        if not tab_id:
            return

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Close Tab", command=lambda: self.close_tab(tab_id))
        menu.tk_popup(event.x_root, event.y_root)

    def get_tab_under_mouse(self, event):
        x, y = event.x, event.y
        try:
            tab_index = self.notebook.index(f"@{x},{y}")
            return self.notebook.tabs()[tab_index]
        except Exception:
            return None


if __name__ == "__main__":
    app = ZipApp()
    app.mainloop()
