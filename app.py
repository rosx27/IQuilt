import os
import subprocess
import json
import tkinter as tk
from tkinter import ttk, filedialog

def get_video_files(folder_path):
    video_files = []
    for file in os.listdir(folder_path):
        if file.endswith(('.mp4', '.avi', '.mkv', '.mov')):
            video_files.append(file)
    return video_files

def take_screenshots(video_path, num_screenshots=36):
    ffprobe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    duration = None
    try:
        duration = float(subprocess.check_output(ffprobe_cmd).decode().strip())
    except Exception as e:
        print(f"Error getting video duration: {e}")

    if duration is not None and duration > 0:
        interval = duration / num_screenshots

        for i in range(num_screenshots):
            timestamp = i * interval
            output_file = os.path.join(temp_folder_path_var.get(), f'output_{timestamp:.2f}.jpg')
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',
                output_file
            ]
            subprocess.run(cmd)

    return duration

def get_video_info(video_path):
    ffprobe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,bit_rate,codec_name,r_frame_rate',
        '-of', 'json',
        video_path
    ]
    try:
        ffprobe_output = subprocess.check_output(ffprobe_cmd).decode().strip()
        video_info = json.loads(ffprobe_output)['streams'][0]
        width, height, bit_rate, video_codec, video_fps = (
            video_info.get('width', 'N/A'),
            video_info.get('height', 'N/A'),
            video_info.get('bit_rate', 'N/A'),
            video_info.get('codec_name', 'N/A'),
            eval(video_info.get('r_frame_rate', '0/1')),
        )
    except Exception as e:
        print(f"Error getting video information: {e}")
        return None

    resolution = f'{width}x{height}' if width != 'N/A' and height != 'N/A' else 'N/A'

    return {
        'resolution': resolution,
        'bit_rate': bit_rate,
        'video_codec': video_codec,
        'video_fps': video_fps,
    }

def get_audio_info(video_path):
    ffprobe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=codec_name,sample_rate',
        '-of', 'json',
        video_path
    ]
    try:
        ffprobe_output = subprocess.check_output(ffprobe_cmd).decode().strip()
        audio_info = json.loads(ffprobe_output)['streams'][0]
        audio_codec, sample_rate = (
            audio_info.get('codec_name', 'N/A'),
            audio_info.get('sample_rate', 'N/A'),
        )
    except Exception as e:
        print(f"Error getting audio information: {e}")
        return None

    return {
        'audio_codec': audio_codec,
        'sample_rate': sample_rate,
    }

def create_image_grid(video_name, folder_path, num_screenshots=36, grid_size=(3, 12), duration=None, margin=10):
    if duration is None or duration <= 0:
        raise ValueError("Invalid duration value")

    video_path = os.path.join(folder_path, video_name)
    video_info = get_video_info(video_path)
    audio_info = get_audio_info(video_path)
    
    if video_info is None or audio_info is None:
        return

    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted_duration = f"{int(hours):02d}:{int(minutes):02d}:{seconds:.2f}"

    images = [os.path.join(temp_folder_path_var.get(), f'output_{i * (duration / num_screenshots):.2f}.jpg') for i in range(num_screenshots)]
    grid_output_file = os.path.join(output_folder_path_var.get(), f'{video_name.split(".")[0]}.jpg')

    title_text = (
        "\n\n\n\n\n\n\n\nVideo Information\n\n"
        f"Filename: {video_name}\n"
        f"Duration: {formatted_duration}; "
        f'Resolution: {video_info["resolution"]}\n'
        f'Bitrate: {video_info["bit_rate"]}; '
        f'Video codec: {video_info["video_codec"]}; '
        f'Frame rate: {video_info["video_fps"]} FPS;\n'
        f'Audio codec: {audio_info["audio_codec"]}; '
        f'Sample rate: {audio_info["sample_rate"]}; '
        f'File size: {os.path.getsize(video_path) / (1024 * 1024):.2f} MB'
    )

    try:
        montage_cmd = [
            'magick',
            'montage',
            '-mode', 'concatenate',
            '-tile', f'{grid_size[0]}x{grid_size[1]}',
            '-geometry', f'+{margin}+{margin}',
            '-background', 'white',
            '-border', '20',
            '-gravity', 'West',
            '-pointsize', '70',
            '-title', f'text {title_text}',
        ] + images + [grid_output_file]
        subprocess.run(montage_cmd)

        for image in images:
            os.remove(image)

    except Exception as e:
        print(f"Error creating image grid: {e}")

def select_folder():
    folder_selected = filedialog.askdirectory()
    folder_path_var.set(folder_selected)

def select_temp_folder():
    folder_selected = filedialog.askdirectory()
    temp_folder_path_var.set(folder_selected)

def select_output_folder():
    folder_selected = filedialog.askdirectory()
    output_folder_path_var.set(folder_selected)

def update_progress_bar(overall_progress_var, video_progress_var, total_videos, current_video_index, video_progress):
    overall_progress = (current_video_index / total_videos) * 100
    overall_progress_var.set(overall_progress)
    video_progress_var.set(video_progress)

def main():
    folder_path = folder_path_var.get()
    temp_folder_path = temp_folder_path_var.get()
    output_folder_path = output_folder_path_var.get()

    video_files = get_video_files(folder_path)
    total_videos = len(video_files)

    overall_progress_var = tk.DoubleVar()
    overall_progress_bar = ttk.Progressbar(root, variable=overall_progress_var, length=300, mode='determinate')
    overall_progress_bar.grid(row=4, column=1, pady=10)

    def process_video(index):
        if index < total_videos:
            video_file = video_files[index]
            video_path = os.path.join(folder_path, video_file)
            duration = take_screenshots(video_path)

            if duration is not None and duration > 0:
                create_image_grid(video_file, folder_path, duration=duration)

            progress = (index + 1) / total_videos * 100
            overall_progress_var.set(progress)
            root.update_idletasks()

            root.after(100, process_video, index + 1)  # Schedule the next video processing after 100 milliseconds
        else:
            overall_progress_var.set(100)

    process_video(0)

# Create the main window
root = tk.Tk()
root.title("Video Grid Generator")

# Variables for folder paths
folder_path_var = tk.StringVar()
temp_folder_path_var = tk.StringVar()
output_folder_path_var = tk.StringVar()

# Set dark mode theme
root.tk_setPalette(background='#2E2E2E', foreground='#FFFFFF', activeBackground='#0066cc', activeForeground='#FFFFFF')

# Style for ttk widgets
style = ttk.Style()
style.configure('TButton', padding=(5, 5, 5, 5), width=20, background='#2E2E2E', foreground='#FFFFFF', activeForeground='#4C8CEA')
style.configure('TEntry', fieldbackground='#404040', foreground='#FFFFFF')
style.configure('TLabel', foreground='#FFFFFF')
style.map('TButton', background=[('active', '#0066cc')])

# UI elements
tk.Label(root, text="Select Video Folder:").grid(row=0, column=0, pady=5, padx=5, sticky='w')
tk.Entry(root, textvariable=folder_path_var, width=50).grid(row=0, column=1, pady=5, padx=5)
ttk.Button(root, text="Browse", command=select_folder).grid(row=0, column=2, pady=5, padx=5)

tk.Label(root, text="Select Temp Folder:").grid(row=1, column=0, pady=5, padx=5, sticky='w')
tk.Entry(root, textvariable=temp_folder_path_var, width=50).grid(row=1, column=1, pady=5, padx=5)
ttk.Button(root, text="Browse", command=select_temp_folder).grid(row=1, column=2, pady=5, padx=5)

tk.Label(root, text="Select Output Folder:").grid(row=2, column=0, pady=5, padx=5, sticky='w')
tk.Entry(root, textvariable=output_folder_path_var, width=50).grid(row=2, column=1, pady=5, padx=5)
ttk.Button(root, text="Browse", command=select_output_folder).grid(row=2, column=2, pady=5, padx=5)

ttk.Button(root, text="Generate Video Grid", command=main).grid(row=3, column=1, pady=10)

# Run the Tkinter main loop
root.mainloop()
