import multiprocessing
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import Progressbar
from PIL import Image
import os
import logging

logging.basicConfig(filename='image_compression.log', level=logging.ERROR)

BATCH_SIZE = 10

def compress_image(input_path, output_path, quality=85):
    try:
        with Image.open(input_path) as img:
            img.save(output_path, optimize=True, quality=quality)
    except Exception as e:
        logging.error(f"Error compressing image: {input_path}\n{str(e)}")

def compress_images(input_paths, output_dir, quality=85, suffix="_compressed"):
    num_images = len(input_paths)
    for i in range(0, num_images, BATCH_SIZE):
        batch_input_paths = input_paths[i:i + BATCH_SIZE]
        batch_output_paths = [get_output_path(input_path, output_dir, suffix) for input_path in batch_input_paths]

        for input_path, output_path in zip(batch_input_paths, batch_output_paths):
            compress_image(input_path, output_path, quality)

        progress_bar['value'] = (i + len(batch_input_paths)) / num_images * 100
        window.update_idletasks()

    messagebox.showinfo("Compression Complete", "Images compressed successfully!")
    progress_bar['value'] = 0

def get_output_path(input_path, output_dir, suffix):
    filename, extension = os.path.splitext(os.path.basename(input_path))
    filename = f"{filename}{suffix}{extension}"
    return os.path.join(output_dir, filename)

def select_images():
    global image_list
    image_paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    for path in image_paths:
        image_list.insert(tk.END, os.path.normpath(path))

def remove_image():
    global image_list
    selections = image_list.curselection()
    for selection in selections[::-1]:  # Reverse order to avoid index issues
        image_list.delete(selection)

def select_output_directory():
    global output_directory, output_directory_label
    output_directory = filedialog.askdirectory()
    output_directory_label.config(text=output_directory)

def compress_selected_images():
    global image_list, output_directory
    image_paths = [os.path.normpath(image_list.get(idx)) for idx in range(image_list.size())]
    if image_paths:
        if not output_directory:
            messagebox.showwarning("Missing Output Directory", "Please select an output directory.")
            return  # Abort compression if output directory is not selected
        threading.Thread(target=compress_images, args=(image_paths, output_directory), daemon=True).start()
    else:
        messagebox.showwarning("Missing Selection", "Please select images.")

# Create the main Tkinter window
window = tk.Tk()
window.title("Image Compression")
window.geometry("400x500")

# Create buttons
select_images_button = tk.Button(window, text="Select Images", command=select_images)
select_images_button.pack(pady=10)

remove_image_button = tk.Button(window, text="Remove Image", command=remove_image)
remove_image_button.pack(pady=5)

select_output_button = tk.Button(window, text="Select Output Directory", command=select_output_directory)
select_output_button.pack(pady=10)

compress_button = tk.Button(window, text="Start Compression", command=compress_selected_images)
compress_button.pack(pady=10)

# Create image list
image_list = tk.Listbox(window, selectmode=tk.MULTIPLE)  # Set selectmode to MULTIPLE
image_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Create output directory label
output_directory_label = tk.Label(window)
output_directory_label.pack(pady=5)

# Create progress bar
progress_bar = Progressbar(window, orient=tk.HORIZONTAL, length=300, mode='determinate')
progress_bar.pack(pady=10)

# Run the Tkinter event loop
window.mainloop()
