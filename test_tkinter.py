import os
import shutil
import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

SESSION_FILE = "last_session.json"
AUTO_SELECT_EXTS = {".dat", ".mat", ".zip", ".xmp", ".log"}

# 🔥 Global flag
skip_all_duplicates = False


# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def get_extensions(folder_path):
    return sorted({
        Path(f).suffix
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f)) and Path(f).suffix
    })


def handle_duplicate(dst):
    global skip_all_duplicates

    if not os.path.exists(dst):
        return dst

    if skip_all_duplicates:
        return None

    win = tk.Toplevel()
    win.title("Duplicate File")
    win.geometry("360x160")
    win.grab_set()

    result = {"choice": None}

    tk.Label(win, text=f"File already exists:\n{os.path.basename(dst)}").pack(pady=10)

    def replace():
        result["choice"] = "replace"
        win.destroy()

    def skip():
        result["choice"] = "skip"
        win.destroy()

    def skip_all():
        global skip_all_duplicates
        skip_all_duplicates = True
        result["choice"] = "skip"
        win.destroy()

    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="Replace", command=replace).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Skip", command=skip).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Skip All", command=skip_all).pack(side="left", padx=5)

    win.wait_window()

    if result["choice"] == "replace":
        return dst
    else:
        return None


# -------------------------------------------------
# Main App
# -------------------------------------------------
class FileRenameApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("File Rename & Copy Tool")
        self.geometry("950x750")

        style = ttk.Style(self)
        style.theme_use("clam")

        self.source_folder = ""
        self.all_files = []
        self.extension_vars = {}
        self.file_widgets = []

        self.create_zip_var = tk.BooleanVar(value=True)
        self.operation_var = tk.StringVar(value="copy")

        self.create_ui()
        self.load_last_session()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def create_ui(self):
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.main = ttk.Frame(self.canvas, padding=10)
        self.canvas.create_window((0, 0), window=self.main, anchor="nw")

        self.main.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self._bind_mousewheel(self.canvas)

        # Step 1
        section1 = ttk.LabelFrame(self.main, text="Step 1: Rename Names", padding=10)
        section1.pack(fill="x", pady=8)

        self.names_text = tk.Text(section1, height=4)
        self.names_text.pack(fill="x")

        btns = ttk.Frame(section1)
        btns.pack(anchor="w", pady=5)
        ttk.Button(btns, text="Save Session", command=self.save_session).pack(side="left", padx=5)
        ttk.Button(btns, text="Load Session", command=self.load_session).pack(side="left", padx=5)

        # Step 2
        section2 = ttk.LabelFrame(self.main, text="Step 2: Destinations", padding=10)
        section2.pack(fill="x", pady=8)

        self.dest_entry = self._browse_row(section2, "Normal Files Destination", self.browse_destination)
        self.new_folder_entry = self._entry_row(section2, "New Folder Name")
        self.zip_files_dest_entry = self._browse_row(section2, "ZIP Files Destination", self.browse_zip_files_dest)
        self.created_zip_dest_entry = self._browse_row(section2, "Created ZIP Destination", self.browse_created_zip_dest)

        # Step 3
        section3 = ttk.LabelFrame(self.main, text="Step 3: Source Folder", padding=10)
        section3.pack(fill="x", pady=8)

        self.source_entry = self._browse_row(section3, "Source Folder", self.browse_source)
        ttk.Button(section3, text="Detect Extensions", command=self.detect_extensions).pack(anchor="w", pady=5)

        # Step 4
        section4 = ttk.LabelFrame(self.main, text="Step 4: Extensions", padding=10)
        section4.pack(fill="x", pady=8)

        self.extensions_frame = ttk.Frame(section4)
        self.extensions_frame.pack(fill="x")

        ttk.Button(section4, text="Load Files", command=self.load_files).pack(pady=5)

        # Step 5
        section5 = ttk.LabelFrame(self.main, text="Step 5: Files", padding=10)
        section5.pack(fill="x", pady=8)

        self.files_frame = ttk.Frame(section5)
        self.files_frame.pack(fill="x")

        # Options
        section6 = ttk.LabelFrame(self.main, text="Options", padding=10)
        section6.pack(fill="x", pady=8)

        ttk.Radiobutton(section6, text="Copy", variable=self.operation_var, value="copy").pack(side="left")
        ttk.Radiobutton(section6, text="Move", variable=self.operation_var, value="move").pack(side="left")
        ttk.Checkbutton(section6, text="Create ZIP", variable=self.create_zip_var).pack(side="left", padx=10)

        # Progress
        self.progress = ttk.Progressbar(self.main, mode="determinate")
        self.progress.pack(fill="x", pady=5)

        self.status_label = ttk.Label(self.main, text="")
        self.status_label.pack(anchor="w")

        self.execute_btn = ttk.Button(self.main, text="Execute", command=self.start_execution)
        self.execute_btn.pack(pady=15)

    def _browse_row(self, parent, label, command):
        ttk.Label(parent, text=label).pack(anchor="w")
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=2)

        entry = ttk.Entry(frame)
        entry.pack(side="left", fill="x", expand=True)
        ttk.Button(frame, text="Browse", command=command).pack(side="left", padx=5)
        return entry

    def _entry_row(self, parent, label):
        ttk.Label(parent, text=label).pack(anchor="w")
        entry = ttk.Entry(parent)
        entry.pack(fill="x", pady=2)
        return entry

    # Mouse scroll
    def _bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", self._on_mousewheel)
        widget.bind_all("<Button-4>", self._on_mousewheel)
        widget.bind_all("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")

    # Logic
    def auto_assign_name(self, filename, names):
        for n in names:
            if n.lower() in filename.lower():
                return n
        return names[0] if names else ""

    def detect_extensions(self):
        for w in self.extensions_frame.winfo_children():
            w.destroy()

        self.extension_vars.clear()

        for ext in get_extensions(self.source_folder):
            var = tk.BooleanVar(value=(ext.lower() in AUTO_SELECT_EXTS))
            ttk.Checkbutton(self.extensions_frame, text=ext, variable=var).pack(side="left", padx=5)
            self.extension_vars[ext] = var

    def load_files(self):
        for w in self.files_frame.winfo_children():
            w.destroy()

        self.file_widgets.clear()

        names = [n.strip() for n in self.names_text.get("1.0", tk.END).splitlines() if n.strip()]
        selected_exts = set(e for e, v in self.extension_vars.items() if v.get())

        for f in self.all_files:
            ext = os.path.splitext(f)[1]
            if ext not in selected_exts:
                continue

            row = ttk.Frame(self.files_frame)
            row.pack(fill="x", pady=2)

            inc = tk.BooleanVar(value=True)
            keep = tk.BooleanVar()
            folder_only = tk.BooleanVar()

            ttk.Checkbutton(row, variable=inc).pack(side="left")
            ttk.Label(row, text=f, width=40).pack(side="left")

            rename = tk.StringVar(value=self.auto_assign_name(f, names))
            ttk.Combobox(row, values=names, textvariable=rename, width=20).pack(side="left")

            ttk.Checkbutton(row, text="Folder only", variable=folder_only).pack(side="left")
            ttk.Checkbutton(row, text="Keep original", variable=keep).pack(side="left")

            self.file_widgets.append((f, inc, keep, folder_only, rename))

    def start_execution(self):
        self.execute_btn.config(state="disabled")
        threading.Thread(target=self.execute, daemon=True).start()

    def execute(self):
        global skip_all_duplicates
        skip_all_duplicates = False

        try:
            normal_dest = os.path.join(self.dest_entry.get(), self.new_folder_entry.get())
            zip_files_dest = self.zip_files_dest_entry.get()
            created_zip_dest = self.created_zip_dest_entry.get()

            os.makedirs(normal_dest, exist_ok=True)
            os.makedirs(zip_files_dest, exist_ok=True)
            os.makedirs(created_zip_dest, exist_ok=True)

            selected = [w for w in self.file_widgets if w[1].get()]
            total = len(selected)
            count = 0

            for f, inc, keep, folder_only, rename in selected:
                count += 1
                self.progress["value"] = (count / total) * 100
                self.status_label.config(text=f"Processing: {f}")
                self.update_idletasks()

                ext = os.path.splitext(f)[1]

                if keep.get():
                    final_name = f
                elif folder_only.get():
                    final_name = f"{self.new_folder_entry.get()}{ext}"
                else:
                    final_name = f"{self.new_folder_entry.get()}_{rename.get()}{ext}"

                src = os.path.join(self.source_folder, f)
                dst = os.path.join(zip_files_dest if ext == ".zip" else normal_dest, final_name)

                dst = handle_duplicate(dst)
                if dst is None:
                    continue

                if self.operation_var.get() == "move":
                    shutil.move(src, dst)
                else:
                    shutil.copy2(src, dst)

            if self.create_zip_var.get():
                zip_path = os.path.join(created_zip_dest, self.new_folder_entry.get() + ".zip")
                zip_path = handle_duplicate(zip_path)
                if zip_path:
                    shutil.make_archive(zip_path.replace(".zip", ""), "zip",
                                        self.dest_entry.get(), self.new_folder_entry.get())

            messagebox.showinfo("Success", "All outputs saved.")

        finally:
            self.execute_btn.config(state="normal")
            self.status_label.config(text="Done")

    # Browse + session
    def browse_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, path)
            self.source_folder = path
            self.all_files = os.listdir(path)

    def browse_destination(self):
        self._set_path(self.dest_entry)

    def browse_zip_files_dest(self):
        self._set_path(self.zip_files_dest_entry)

    def browse_created_zip_dest(self):
        self._set_path(self.created_zip_dest_entry)

    def _set_path(self, entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
            self.save_last_session()

    def save_last_session(self):
        json.dump({
            "dest_folder": self.dest_entry.get(),
            "zip_files_dest": self.zip_files_dest_entry.get(),
            "created_zip_dest": self.created_zip_dest_entry.get()
        }, open(SESSION_FILE, "w"), indent=4)

    def load_last_session(self):
        if os.path.exists(SESSION_FILE):
            data = json.load(open(SESSION_FILE))
            self.dest_entry.insert(0, data.get("dest_folder", ""))
            self.zip_files_dest_entry.insert(0, data.get("zip_files_dest", ""))
            self.created_zip_dest_entry.insert(0, data.get("created_zip_dest", ""))

    def save_session(self):
        names = [n.strip() for n in self.names_text.get("1.0", tk.END).splitlines() if n.strip()]
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            json.dump({"rename_names": names}, open(path, "w"), indent=4)

    def load_session(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            names = json.load(open(path)).get("rename_names", [])
            self.names_text.delete("1.0", tk.END)
            self.names_text.insert(tk.END, "\n".join(names))


if __name__ == "__main__":
    FileRenameApp().mainloop()