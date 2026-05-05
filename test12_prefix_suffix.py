import os
import shutil
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

SESSION_FILE = "last_session.json"

# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def get_extensions(folder_path):
    return sorted({
        Path(f).suffix
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f)) and Path(f).suffix
    })


# -------------------------------------------------
# Main App
# -------------------------------------------------
class FileRenameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Rename & Copy Tool")
        self.geometry("900x700")

        self.source_folder = ""
        self.extension_vars = {}
        self.file_widgets = []

        self.create_zip_var = tk.BooleanVar(value=True)
        self.operation_var = tk.StringVar(value="copy")

        self.create_ui()
        self.load_last_session()

    # -------------------------------------------------
    # UI Layout
    # -------------------------------------------------
    def create_ui(self):
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.main = ttk.Frame(canvas, padding=10)
        canvas.create_window((0, 0), window=self.main, anchor="nw")

        self.main.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        self._bind_mousewheel(canvas)

        # ---------- STEP 1 ----------
        ttk.Label(self.main, text="Step 1: Enter Rename Names").pack(anchor="w")
        self.names_text = tk.Text(self.main, height=5)
        self.names_text.pack(fill="x", pady=5)

        step1_btns = ttk.Frame(self.main)
        step1_btns.pack(anchor="w", pady=5)
        ttk.Button(step1_btns, text="Save Session", command=self.save_session).pack(side="left", padx=5)
        ttk.Button(step1_btns, text="Load Session", command=self.load_session).pack(side="left", padx=5)

        # ---------- STEP 2 ----------
        ttk.Label(self.main, text="Step 2: Destination Folder (Normal Files)").pack(anchor="w")
        frame = ttk.Frame(self.main)
        frame.pack(fill="x")
        self.dest_entry = ttk.Entry(frame)
        self.dest_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(frame, text="Browse", command=self.browse_destination).pack(side="left", padx=5)

        ttk.Label(self.main, text="New Folder Name").pack(anchor="w")
        self.new_folder_entry = ttk.Entry(self.main)
        self.new_folder_entry.pack(fill="x", pady=5)

        # ---------- STEP 5 ----------
        ttk.Label(self.main, text="ZIP Files Destination (Step 5)").pack(anchor="w")
        frame = ttk.Frame(self.main)
        frame.pack(fill="x")
        self.zip_files_dest_entry = ttk.Entry(frame)
        self.zip_files_dest_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(frame, text="Browse", command=self.browse_zip_files_dest).pack(side="left", padx=5)

        # ---------- STEP 6 ----------
        ttk.Label(self.main, text="Created ZIP Destination (Step 6)").pack(anchor="w")
        frame = ttk.Frame(self.main)
        frame.pack(fill="x")
        self.created_zip_dest_entry = ttk.Entry(frame)
        self.created_zip_dest_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(frame, text="Browse", command=self.browse_created_zip_dest).pack(side="left", padx=5)

        # ---------- STEP 3 ----------
        ttk.Label(self.main, text="Step 3: Source Folder").pack(anchor="w", pady=(10, 0))
        frame = ttk.Frame(self.main)
        frame.pack(fill="x")
        self.source_entry = ttk.Entry(frame)
        self.source_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(frame, text="Browse", command=self.browse_source).pack(side="left", padx=5)

        ttk.Button(self.main, text="Detect Extensions", command=self.detect_extensions).pack(anchor="w", pady=6)

        # ---------- STEP 4 ----------
        ttk.Label(self.main, text="Step 4: Detect & Select Extensions").pack(anchor="w")
        self.extensions_frame = ttk.Frame(self.main)
        self.extensions_frame.pack(fill="x", pady=5)
        ttk.Button(self.main, text="Load Files for Selected Extensions",
                   command=self.load_files).pack(pady=8)

        # ---------- STEP 5 ----------
        ttk.Label(self.main, text="Step 5: Select Files and Assign Names").pack(anchor="w")
        self.files_frame = ttk.Frame(self.main)
        self.files_frame.pack(fill="x", pady=5)

        # ---------- COPY / MOVE ----------
        ttk.Label(self.main, text="Operation").pack(anchor="w", pady=(10, 0))
        op_frame = ttk.Frame(self.main)
        op_frame.pack(anchor="w")
        ttk.Radiobutton(op_frame, text="Copy", variable=self.operation_var, value="copy").pack(side="left")
        ttk.Radiobutton(op_frame, text="Move", variable=self.operation_var, value="move").pack(side="left")

        # ---------- STEP 6 ----------
        ttk.Checkbutton(self.main, text="Create ZIP file",
                        variable=self.create_zip_var).pack(anchor="w", pady=5)
        ttk.Button(self.main, text="Execute", command=self.execute).pack(pady=15)

    # -------------------------------------------------
    # Mouse wheel support
    # -------------------------------------------------
    def _bind_mousewheel(self, canvas):
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    # -------------------------------------------------
    # Auto‑persistent Destinations
    # -------------------------------------------------
    def save_last_session(self):
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "dest_folder": self.dest_entry.get(),
                "zip_files_dest": self.zip_files_dest_entry.get(),
                "created_zip_dest": self.created_zip_dest_entry.get()
            }, f, indent=4)

    def load_last_session(self):
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.dest_entry.insert(0, data.get("dest_folder", ""))
                self.zip_files_dest_entry.insert(0, data.get("zip_files_dest", ""))
                self.created_zip_dest_entry.insert(0, data.get("created_zip_dest", ""))

    # -------------------------------------------------
    # Browse dialogs
    # -------------------------------------------------
    def browse_destination(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, path)
            self.save_last_session()

    def browse_zip_files_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.zip_files_dest_entry.delete(0, tk.END)
            self.zip_files_dest_entry.insert(0, path)
            self.save_last_session()

    def browse_created_zip_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.created_zip_dest_entry.delete(0, tk.END)
            self.created_zip_dest_entry.insert(0, path)
            self.save_last_session()

    def browse_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, path)
            self.source_folder = path

    # -------------------------------------------------
    # Session Save / Load
    # -------------------------------------------------
    def save_session(self):
        names = [n.strip() for n in self.names_text.get("1.0", tk.END).splitlines() if n.strip()]
        if not names:
            messagebox.showwarning("Warning", "No rename names to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON files", "*.json")])
        if path:
            json.dump({"rename_names": names}, open(path, "w", encoding="utf-8"), indent=4)

    def load_session(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            names = json.load(open(path, "r", encoding="utf-8")).get("rename_names", [])
            self.names_text.delete("1.0", tk.END)
            self.names_text.insert(tk.END, "\n".join(names))

    # -------------------------------------------------
    # Core logic
    # -------------------------------------------------
    def detect_extensions(self):
        if not self.source_folder:
            messagebox.showwarning("Warning", "Please select a source folder first.")
            return
        for w in self.extensions_frame.winfo_children():
            w.destroy()
        self.extension_vars.clear()
        for ext in get_extensions(self.source_folder):
            var = tk.BooleanVar()
            ttk.Checkbutton(self.extensions_frame, text=ext, variable=var).pack(side="left", padx=5)
            self.extension_vars[ext] = var

    def load_files(self):
        for w in self.files_frame.winfo_children():
            w.destroy()
        self.file_widgets.clear()

        names = [n.strip() for n in self.names_text.get("1.0", tk.END).splitlines() if n.strip()]
        selected_exts = [e for e, v in self.extension_vars.items() if v.get()]

        for f in os.listdir(self.source_folder):
            if Path(f).suffix not in selected_exts:
                continue
            row = ttk.Frame(self.files_frame)
            row.pack(fill="x")

            inc = tk.BooleanVar(value=True)
            keep = tk.BooleanVar()
            ttk.Checkbutton(row, variable=inc).pack(side="left")
            ttk.Label(row, text=f).pack(side="left", expand=True, fill="x")
            ttk.Checkbutton(row, text="Keep original", variable=keep).pack(side="left")

            rename = tk.StringVar(value=names[0])
            ttk.Combobox(row, values=names, textvariable=rename,
                         width=20, state="readonly").pack(side="left")

            self.file_widgets.append((f, inc, keep, rename))

    def execute(self):
        normal_dest = os.path.join(self.dest_entry.get(), self.new_folder_entry.get())
        zip_files_dest = self.zip_files_dest_entry.get()
        created_zip_dest = self.created_zip_dest_entry.get()

        os.makedirs(normal_dest, exist_ok=True)
        os.makedirs(zip_files_dest, exist_ok=True)
        os.makedirs(created_zip_dest, exist_ok=True)

        for f, inc, keep, rename in self.file_widgets:
            if not inc.get():
                continue

            if keep.get():
                final_name = f
            else:
                final_name = f"{self.new_folder_entry.get()}_{rename.get()}{Path(f).suffix}"

            src = os.path.join(self.source_folder, f)
            dst = os.path.join(zip_files_dest if Path(f).suffix == ".zip" else normal_dest, final_name)

            if self.operation_var.get() == "move":
                shutil.move(src, dst)
            else:
                shutil.copy2(src, dst)

        if self.create_zip_var.get():
            shutil.make_archive(
                os.path.join(created_zip_dest, self.new_folder_entry.get()),
                "zip",
                self.dest_entry.get(),
                self.new_folder_entry.get()
            )

        messagebox.showinfo("Success", "All outputs saved.")


# -------------------------------------------------
# Run App
# -------------------------------------------------
if __name__ == "__main__":
    FileRenameApp().mainloop()