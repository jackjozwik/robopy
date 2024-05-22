import os
import tkinter as tk
import subprocess
import tempfile
import threading
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import messagebox, filedialog, ttk



class BackupTool(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("RoboPy")
        self.geometry("600x700")

        # Set the icon for the application
        

        self.robocopy_process = None
        self.exported = False
        
        # Source path frame
        source_frame = ttk.LabelFrame(self, text="Source Path")
        source_frame.pack(pady=10, padx=10, fill="x")
        self.source_label = tk.Label(source_frame, text="Drag Source Directory Here", relief="solid", height=2)
        self.source_label.pack(side="left", fill='x', expand=True, padx=10, pady=5)
        self.source_browse_button = tk.Button(source_frame, text="Browse", command=self.browse_source)
        self.source_browse_button.pack(side="right", padx=10, pady=5)
        self.source_label.drop_target_register(DND_FILES)
        self.source_label.dnd_bind('<<Drop>>', self.on_source_drop)

        # Destination path frame
        destination_frame = ttk.LabelFrame(self, text="Destination Path")
        destination_frame.pack(pady=10, padx=10, fill="x")
        self.destination_label = tk.Label(destination_frame, text="Drag Destination Directory Here", relief="solid", height=2)
        self.destination_label.pack(side="left", fill='x', expand=True, padx=10, pady=5)
        self.destination_browse_button = tk.Button(destination_frame, text="Browse", command=self.browse_destination)
        self.destination_browse_button.pack(side="right", padx=10, pady=5)
        self.destination_label.drop_target_register(DND_FILES)
        self.destination_label.dnd_bind('<<Drop>>', self.on_destination_drop)

        # Options frame
        options_frame = ttk.LabelFrame(self, text="Options")
        options_frame.pack(pady=10, padx=10, fill="x")

        # Multithread input
        tk.Label(options_frame, text="Multithread (MT)").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.mt_var = tk.IntVar(value=32)
        tk.Spinbox(options_frame, from_=1, to_=128, textvariable=self.mt_var).grid(row=0, column=1, padx=10, pady=5, sticky='w')

        # Checkboxes for robocopy options
        self.v_var = tk.BooleanVar(value=True)
        self.z_var = tk.BooleanVar(value=True)
        self.e_var = tk.BooleanVar(value=True)
        self.r_var = tk.IntVar(value=5)
        self.w_var = tk.IntVar(value=3)
        
        tk.Checkbutton(options_frame, text="Verbose (V)", variable=self.v_var).grid(row=1, column=0, padx=10, pady=5, sticky='w')
        tk.Checkbutton(options_frame, text="Restartable (Z)", variable=self.z_var).grid(row=1, column=1, padx=10, pady=5, sticky='w')
        tk.Checkbutton(options_frame, text="Sub-directories (E)", variable=self.e_var).grid(row=1, column=2, padx=10, pady=5, sticky='w')

        tk.Label(options_frame, text="Retries (R)").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        tk.Spinbox(options_frame, from_=0, to_=100, textvariable=self.r_var).grid(row=2, column=1, padx=10, pady=5, sticky='w')

        tk.Label(options_frame, text="Wait (W)").grid(row=2, column=2, padx=10, pady=5, sticky='w')
        tk.Spinbox(options_frame, from_=0, to_=60, textvariable=self.w_var).grid(row=2, column=3, padx=10, pady=5, sticky='w')

        buttons_frame = tk.Frame(self)
        buttons_frame.pack(pady=20, padx=10, fill='x', expand=True)

        buttons_frame = tk.Frame(self)
        buttons_frame.pack(pady=20, padx=10, fill='x', expand=True)

        self.backup_button = tk.Button(buttons_frame, text="Start Backup", command=self.backup)
        self.backup_button.pack(side="left", padx=10, fill='x', expand=True)

        self.cancel_button = tk.Button(buttons_frame, text="Cancel", command=self.cancel_backup, state='disabled')
        self.cancel_button.pack(side="left", padx=10, fill='x', expand=True)

        self.source_path = ""
        self.destination_path = ""

        self.log_frame = ttk.LabelFrame(self, text="Log")
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = tk.Text(self.log_frame, state='disabled', height=10)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        self.export_log_button = tk.Button(self, text="Export Log", command=self.export_log, state='disabled')
        self.export_log_button.pack(pady=10, padx=10, fill='x', expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)


        

    def browse_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_path = path
            self.source_label.config(text=self.source_path)

    def browse_destination(self):
        path = filedialog.askdirectory()
        if path:
            self.destination_path = path
            self.destination_label.config(text=self.destination_path)

    
    def on_source_drop(self, event):
        path = event.data.strip('{}')
        if os.path.isdir(path):
            self.source_path = path
            self.source_label.config(text=self.source_path)
        else:
            messagebox.showerror("Error", "Please drop a directory, not a file.")

    def on_destination_drop(self, event):
        path = event.data.strip('{}')
        if os.path.isdir(path):
            self.destination_path = path
            self.destination_label.config(text=self.destination_path)
        else:
            messagebox.showerror("Error", "Please drop a directory, not a file.")


    def backup(self):
        if self.source_path and self.destination_path:
            if messagebox.askyesno("Confirmation", f"Are you sure you want to copy {self.source_path} \nto \n{self.destination_path}?"):
                # Disable the Export Log button
                self.export_log_button.config(state='disabled')

                # Create a thread to run the backup
                backup_thread = threading.Thread(target=self.run_backup)
                backup_thread.start()
        else:
            messagebox.showwarning("Warning", "Please select both source and destination directories.")


    def run_backup(self):
        mt = self.mt_var.get()
        v = '/V' if self.v_var.get() else ''
        z = '/Z' if self.z_var.get() else ''
        e = '/E' if self.e_var.get() else ''
        r = self.r_var.get()
        w = self.w_var.get()
        log_dir = tempfile.gettempdir()
        log_path = os.path.join(log_dir, 'robocopy_log.txt')
        command = f'robocopy "{self.source_path}" "{self.destination_path}" /MT:{mt} {v} {z} {e} /R:{r} /W:{w} /TEE /LOG:"{log_path}"'
        self.log(f"Executing: {command}")
        try:
            self.cancel_button.config(state='normal')
            self.robocopy_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Read stdout line by line
            while self.robocopy_process and self.robocopy_process.poll() is None:
                line = self.robocopy_process.stdout.readline()
                if line:
                    self.log(line.strip())

            # Ensure all remaining output is read
            if self.robocopy_process:
                for line in self.robocopy_process.stdout:
                    self.log(line.strip())

                self.robocopy_process.wait()
                if self.robocopy_process.returncode == 1:
                    self.log(f"Backup from {self.source_path} to {self.destination_path} completed!\n")
                else:
                    self.log(f"Robocopy exited with code {self.robocopy_process.returncode}")

            self.verify_backup()  # Call verification after backup

        except Exception as e:
            self.log(f"Error: {str(e)}")
        finally:
            self.cancel_button.config(state='disabled')
            self.robocopy_process = None

            self.export_log_button.config(state='normal')


    def get_directory_size_and_count(self, directory):
        total_size = 0
        file_count = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
                file_count += 1
        return total_size, file_count

    def verify_backup(self):
        if self.source_path and self.destination_path:
            source_size, source_count = self.get_directory_size_and_count(self.source_path)
            dest_size, dest_count = self.get_directory_size_and_count(self.destination_path)
            self.log(f"Source - Size: {source_size} bytes, Files: {source_count}")
            self.log(f"Destination - Size: {dest_size} bytes, Files: {dest_count}")
            if source_size == dest_size and source_count == dest_count:
                self.log("Verification successful: Source and destination directories match.")
            else:
                self.log("Verification failed: Source and destination directories do not match.")
                self.log(f"Source - Size: {source_size} bytes, Files: {source_count}")
                self.log(f"Destination - Size: {dest_size} bytes, Files: {dest_count}")
        else:
            messagebox.showwarning("Warning", "Please select both source and destination directories.")


    def cancel_backup(self):
        if self.robocopy_process:
            self.robocopy_process.terminate()
            self.robocopy_process = None  # Ensure this is set to None
            self.log("Backup process terminated by user.")
            self.cancel_button.config(state='disabled')


    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + '\n')
        self.log_text.config(state='disabled')
        self.log_text.see('end')  # Scroll to the end


    def export_log(self):
        log_content = self.log_text.get('1.0', 'end').strip()
        if log_content:
            default_file_name = "log.txt"
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_file_name, filetypes=[("Text files", "*.txt")])
            if file_path:
                with open(file_path, 'w') as log_file:
                    log_file.write(log_content)
                messagebox.showinfo("Export Log", f"Log exported to {file_path}")
                self.exported = True
        else:
            messagebox.showwarning("Warning", "Log is empty.")


    def on_closing(self):
        log_content = self.log_text.get('1.0', 'end').strip()
        if log_content and not self.exported:
            if messagebox.askyesno("Exit", "Are you sure you want to exit without exporting logs?"):
                self.destroy()
        else:
            self.destroy()



if __name__ == '__main__':
    app = BackupTool()
    app.mainloop()
