import math
import os
import tkinter as tk
import subprocess
import tempfile
import threading
from tkinter import Scrollbar, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import messagebox, filedialog, ttk
import queue
import time


class BackupTool(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("RoboPy")
        self.geometry("600x700")

        #Do NOT Set the icon for the application
        self.start_time = None
        self.robocopy_process = None
        self.exported = False

        self.source_path = ""
        self.destination_path = ""
        self.exclude_var = tk.StringVar(value="")


        # Create a PanedWindow
        paned_window = tk.PanedWindow(self, orient="vertical")
        paned_window.pack(fill="both", expand=True)

        # Create a frame for the top section
        top_frame = tk.Frame(paned_window)
        paned_window.add(top_frame)

        # Source path frame
        source_frame = ttk.LabelFrame(top_frame, text="Source Path")
        source_frame.pack(pady=10, padx=10, fill="x")
        self.source_label = tk.Label(source_frame, text="Drag Source Directory Here", relief="solid", height=2)
        self.source_label.pack(side="left", fill='x', expand=True, padx=10, pady=5)
        self.source_browse_button = tk.Button(source_frame, text="Browse", command=self.browse_source)
        self.source_browse_button.pack(side="right", padx=10, pady=5)
        self.source_label.drop_target_register(DND_FILES)
        self.source_label.dnd_bind('<<Drop>>', self.on_source_drop)

        # Destination path frame
        destination_frame = ttk.LabelFrame(top_frame, text="Destination Path")
        destination_frame.pack(pady=10, padx=10, fill="x")
        self.destination_label = tk.Label(destination_frame, text="Drag Destination Directory Here", relief="solid", height=2)
        self.destination_label.pack(side="left", fill='x', expand=True, padx=10, pady=5)
        self.destination_browse_button = tk.Button(destination_frame, text="Browse", command=self.browse_destination)
        self.destination_browse_button.pack(side="right", padx=10, pady=5)
        self.destination_label.drop_target_register(DND_FILES)
        self.destination_label.dnd_bind('<<Drop>>', self.on_destination_drop)

        # Exclude directories frame
        exclude_frame = ttk.LabelFrame(top_frame, text="Exclude Directories")
        exclude_frame.pack(pady=10, padx=10, fill="x")
        self.exclude_text = tk.Text(exclude_frame, height=2, relief="solid", width=40)
        self.exclude_text.pack(side="left", fill='x', expand=True, padx=10, pady=5)
        self.exclude_browse_button = tk.Button(exclude_frame, text="Browse", command=self.browse_exclude)
        self.exclude_browse_button.pack(side="right", padx=10, pady=5)
        self.exclude_text.drop_target_register(DND_FILES)
        self.exclude_text.dnd_bind('<<Drop>>', self.on_exclude_drop)

        # Options frame
        options_frame = ttk.LabelFrame(top_frame, text="Options")
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

        # Buttons frame
        buttons_frame = tk.Frame(top_frame)
        buttons_frame.pack(pady=20, padx=10, fill='x', expand=True)

        self.backup_button = tk.Button(buttons_frame, text="Start Backup", command=self.backup)
        self.backup_button.pack(side="left", padx=10, fill='x', expand=True)

        self.cancel_button = tk.Button(buttons_frame, text="Cancel", command=self.cancel_backup, state='disabled')
        self.cancel_button.pack(side="left", padx=10, fill='x', expand=True)

        self.export_log_button = tk.Button(buttons_frame, text="Export Log", command=self.export_log, state='disabled')
        self.export_log_button.pack(side="left", padx=10, fill='x', expand=True)

        # Log frame
        self.log_frame = ttk.LabelFrame(paned_window, text="Log")
        self.log_frame.pack(pady=10, padx=10, fill="x")
        paned_window.add(self.log_frame)

        self.log_text_frame = ttk.Frame(self.log_frame)
        self.log_text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        y=Scrollbar(self.log_text_frame, orient='vertical')
        y.pack(side="right", fill='y')

        self.log_text = tk.Text(self.log_text_frame, state='disabled', height=10, wrap='word', yscrollcommand=y.set)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        y.config(command=self.log_text.yview)

        self.sizegrip = ttk.Sizegrip(self.log_frame)
        self.sizegrip.pack(side="right", anchor="se")


        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Queue to hold log messages
        self.log_queue = queue.Queue()
        self.after(50, self.process_log_queue)

        

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

    def browse_exclude(self):
        directory = filedialog.askdirectory()
        if directory:
            current_excludes = self.exclude_text.get("1.0", tk.END).strip()
            if current_excludes:
                current_excludes = current_excludes.split(",")
            else:
                current_excludes = []
            current_excludes.append(directory)
            self.exclude_text.delete("1.0", tk.END)  # Clear the current text
            self.exclude_text.insert("1.0", ",".join(current_excludes))  # Insert the new list of directories
    
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

    def on_exclude_drop(self, event):
        print("Dropped data:", event.data)  # Continue logging the raw data for verification
        new_excludes = self.parse_dropped_paths(event.data)
        print("Parsed new excludes:", new_excludes)  # Verify parsed paths are correct

        current_excludes = self.exclude_text.get("1.0", "end-1c").strip()
        if current_excludes and new_excludes:
            formatted_excludes = ", ".join([current_excludes] + new_excludes)
        else:
            formatted_excludes = ", ".join(new_excludes)

        self.exclude_text.delete("1.0", "end")  # Clear the current text
        self.exclude_text.insert("1.0", formatted_excludes)  # Insert the formatted list of directories


    def parse_dropped_paths(self, paths):
        # Normalize the input by ensuring all path dividers are consistent
        paths = paths.strip("{}").replace('}{', ',')
        # Split on the comma, which should now correctly separate all paths
        paths_list = [path.strip() for path in paths.split(',')]
        # Additional handling for cases where paths might not have been split correctly
        if len(paths_list) == 1:
            # If only one path and it contains spaces potentially as separate paths, split further
            # First, handle potential trailing spaces and single curly braces
            single_path = paths_list[0].replace('} ', ', ').replace(' {', ', ')
            # Now split if there are any commas introduced or spaces that imply separation
            paths_list = [path.strip() for path in single_path.split(',') if path.strip()]
        return paths_list


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
        self.start_time = time.time()

        mt = self.mt_var.get()
        v = '/V' if self.v_var.get() else ''
        z = '/Z' if self.z_var.get() else ''
        e = '/E' if self.e_var.get() else ''
        r = self.r_var.get()
        w = self.w_var.get()

        exclude_dirs = [path.strip().replace('/', '\\') for path in self.exclude_text.get("1.0", "end-1c").split(',') if path.strip()]
        exclude_params = ' '.join([f'/XD "{d}"' for d in exclude_dirs])

        log_dir = tempfile.gettempdir()
        log_path = os.path.join(log_dir, 'robocopy_log.txt')
        command = f'robocopy "{self.source_path}" "{self.destination_path}" /MT:{mt} {exclude_params} {v} {z} {e} /R:{r} /W:{w} /TEE /LOG:"{log_path}"'

        self.log_queue.put(f"Starting backup from {self.source_path} to {self.destination_path}\n")
        self.log_queue.put(f"Executing: {command}")

        try:
            self.backup_button.config(state='disabled')
            self.cancel_button.config(state='normal')
            self.robocopy_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Read stdout line by line
            while self.robocopy_process and self.robocopy_process.poll() is None:
                line = self.robocopy_process.stdout.readline()
                if line:
                    self.log_queue.put(line.strip())

            # Ensure all remaining output is read
            if self.robocopy_process:
                for line in self.robocopy_process.stdout:
                    self.log_queue.put(line.strip())

                self.robocopy_process.wait()
                if self.robocopy_process.returncode == 1:
                    end_time = time.time()
                    total_time = end_time - self.start_time

                    hours, remainder = divmod(total_time, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    self.log_queue.put(f"Backup from {self.source_path} to {self.destination_path} completed!\n")
                    self.log_queue.put(f"Total time to copy: {int(hours)}h {int(minutes)}m {int(seconds)}s\n")
                else:
                    self.log_queue.put(f"Robocopy exited with code {self.robocopy_process.returncode}")

            self.verify_backup()  # Call verification after backup

        except Exception as e:
            self.log_queue.put(f"Error: {str(e)}")
        finally:
            self.backup_button.config(state='normal')
            self.cancel_button.config(state='disabled')
            self.export_log_button.config(state='normal')
            self.robocopy_process = None


    def get_directory_size_and_count(self, directory):
        total_size = 0
        file_count = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
                file_count += 1
        return total_size, file_count


    def convert_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"


    def verify_backup(self):
        if self.source_path and self.destination_path:
            source_size, source_count = self.get_directory_size_and_count(self.source_path)
            dest_size, dest_count = self.get_directory_size_and_count(self.destination_path)

            source_size_readable = self.convert_size(source_size)
            dest_size_readable = self.convert_size(dest_size)

            self.log_queue.put(f"Source - Size: {source_size_readable} bytes, Files: {source_count}")
            self.log_queue.put(f"Destination - Size: {dest_size_readable} bytes, Files: {dest_count}")

            if source_size == dest_size and source_count == dest_count:
                self.log_queue.put("Verification successful: Source and destination directories match.")
            else:
                self.log_queue.put("Verification failed: Source and destination directories do not match.")
        else:
            messagebox.showwarning("Warning", "Please select both source and destination directories.")


    def cancel_backup(self):
        if self.robocopy_process:
            self.robocopy_process.terminate()
            self.robocopy_process = None  # Ensure this is set to None
            self.log_queue.put("Backup cancelled.\n")
            self.cancel_button.config(state='disabled')
            self.export_log_button.config(state='normal')


    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + '\n')
        self.log_text.config(state='disabled')
        self.log_text.see('end')  # Scroll to the end


    def process_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self.log(message)
        self.after(50, self.process_log_queue)


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
