import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
from nptdms import TdmsFile
import numpy as np
import os
import xml.etree.ElementTree as ET

class TDMSImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TDMS Image Viewer")

        # Ask user to select the XML file
        xml_file_path = filedialog.askopenfilename(title="Select XML File", filetypes=[("XML files", "*.xml")])
        if not xml_file_path:
            print("No file selected. Exiting.")
            root.quit()
            return

        # Read XML file to get experimental parameters
        self.experiment_name, self.pixels_x, self.pixels_y = self.read_xml_parameters(xml_file_path)
        xml_directory = os.path.dirname(xml_file_path)
        tdms_file_path = os.path.join(xml_directory, f"{self.experiment_name}.tdms")

        # Load TDMS file metadata
        self.tdms_file = TdmsFile.read(tdms_file_path)
        self.data_group = self.tdms_file['Data']
        self.num_images = len([ch for ch in self.data_group.channels() if ch.name.startswith('frame')])

        # Load and adjust timestamps
        self.timestamps = self.data_group['timestamps (ns)'].data
        self.timestamps = (self.timestamps - self.timestamps.min()) / 1e9  # Convert to seconds and reset to start from zero

        # Calculate global min and max pixel values
        self.global_min, self.global_max = self.calculate_global_min_max()

        # Setup GUI components
        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        root.attributes('-fullscreen', True)

        self.frame_label = tk.Label(root, text="Frame: ")
        self.frame_label.pack()
        
        self.timestamp_label = tk.Label(root, text="Time: ")
        self.timestamp_label.pack()
        
        self.piezo_label = tk.Label(root, text="Piezo Position: ")
        self.piezo_label.pack()
        
        # Create a frame for the time slider and its title
        time_slider_frame = tk.Frame(root)
        time_slider_frame.pack(pady=10)
        time_slider_title = tk.Label(time_slider_frame, text="Time Slider")
        time_slider_title.pack()
        self.time_slider = ttk.Scale(time_slider_frame, from_=0, to=99, orient='horizontal', command=self.update_image)
        self.time_slider.pack(padx=20, fill='x')
        
        # Create a frame for the z slider and its title
        z_slider_frame = tk.Frame(root)
        z_slider_frame.pack(pady=10)
        z_slider_title = tk.Label(z_slider_frame, text="Z Slider")
        z_slider_title.pack()
        self.z_slider = ttk.Scale(z_slider_frame, from_=0, to=49, orient='horizontal', command=self.update_image)
        self.z_slider.pack(padx=20, fill='x')
        
        # Function to update the slider widths
        def update_slider_widths(event):
            window_width = root.winfo_width()
            slider_width = int(window_width * 0.8)
            self.time_slider.config(length=slider_width)
            self.z_slider.config(length=slider_width)
        
        # Bind the configure event to update the slider widths when the window is resized
        root.bind('<Configure>', update_slider_widths)
        
        # Initialize zoom level
        self.zoom_level = 1.0
        
        # Bind mouse wheel to zoom function
        self.canvas.bind("<MouseWheel>", self.zoom)
        
        # Display the first image
        self.update_image(0)

    def read_xml_parameters(self, xml_file_path):
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        namespace = {'ns': 'http://www.ni.com/LVData'}

        # Debug print to check XML structure
        print(ET.tostring(root, encoding='utf8').decode('utf8'))

        experiment_name = root.find(".//ns:Cluster/ns:Cluster/ns:String[ns:Name='Experiment Name']/ns:Val", namespace).text
        pixels_x = int(root.find(".//ns:Cluster/ns:Cluster[ns:Name='Pixel Count']/ns:U32[ns:Name='Pixels in X']/ns:Val", namespace).text)
        pixels_y = int(root.find(".//ns:Cluster/ns:Cluster[ns:Name='Pixel Count']/ns:U32[ns:Name='Pixels in Y']/ns:Val", namespace).text)

        return experiment_name, pixels_x, pixels_y

    def calculate_global_min_max(self):
        min_val = float('inf')
        max_val = float('-inf')
        for i in range(self.num_images):
            channel_name = f'frame {i}'
            image_data = self.data_group[channel_name].data.astype(np.uint16)
            min_val = min(min_val, image_data.min())
            max_val = max(max_val, image_data.max())
        print(f"Global min pixel value: {min_val}")
        print(f"Global max pixel value: {max_val}")
        return min_val, max_val

    def update_image(self, _):
        time_index = int(float(self.time_slider.get()))
        z_index = int(float(self.z_slider.get()))
        index = time_index * 50 + z_index
        channel_name = f'frame {index}'
        print(f"Loading {channel_name}")

        try:
            image_data = self.data_group[channel_name].data.astype(np.uint16)
            print(f"Image data type: {type(image_data)}")
            print(f"Image data length: {len(image_data)}")

            timestamp = self.timestamps[index]
            piezo_position = self.data_group['PI pos (um)'].data[index]

            print(f"Timestamp: {timestamp}")
            print(f"Piezo Position: {piezo_position}")

            # Reshape image data
            image_data = image_data[:2*self.pixels_x*self.pixels_y]  # Truncate the array to the first 2 * pixels_x * pixels_y elements
            green_channel = np.reshape(image_data[:self.pixels_x*self.pixels_y], (self.pixels_y, self.pixels_x))  # First half for green channel
            red_channel = np.reshape(image_data[self.pixels_x*self.pixels_y:], (self.pixels_y, self.pixels_x))  # Second half for red channel
            print(f"Reshaped green channel shape: {green_channel.shape}")
            print(f"Reshaped red channel shape: {red_channel.shape}")

            self.green_channel = green_channel
            self.red_channel = red_channel
            self.apply_normalization()

            # Update labels
            self.frame_label.config(text=f"Frame: {index}")
            self.timestamp_label.config(text=f"Timestamp: {timestamp:.2f} s")
            self.piezo_label.config(text=f"Piezo Position: {piezo_position}")
        except KeyError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def apply_normalization(self):
        zoom = self.zoom_level
        print(f"Applying normalization with zoom={zoom}")

        # Normalize to 0-255 using global min and max
        normalized_green = ((self.green_channel - self.global_min) / (self.global_max - self.global_min) * 255).astype(np.uint8)
        normalized_red = ((self.red_channel - self.global_min) / (self.global_max - self.global_min) * 255).astype(np.uint8)

        # Create RGB image with the green and red channels
        blue_channel = np.zeros_like(normalized_green)
        rgb_image = np.stack((normalized_red, normalized_green, blue_channel), axis=-1)

        # Convert image data to PIL Image and then to ImageTk
        image = Image.fromarray(rgb_image)

        # Apply zoom without antialiasing
        width, height = image.size
        image = image.resize((int(width * zoom), int(height * zoom)))

        self.photo = ImageTk.PhotoImage(image)

        # Update canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def zoom(self, event):
        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Get original image size
        original_width, original_height = self.green_channel.shape[1], self.green_channel.shape[0]

        # Calculate maximum zoom level
        max_zoom_width = canvas_width / original_width
        max_zoom_height = canvas_height / original_height
        max_zoom_level = min(max_zoom_width, max_zoom_height)

        # Zoom in or out
        if event.delta > 0:
            self.zoom_level = min(self.zoom_level * 1.1, max_zoom_level)
        else:
            self.zoom_level = max(self.zoom_level / 1.1, 1.0)

        self.apply_normalization()

if __name__ == "__main__":
    root = tk.Tk()
    app = TDMSImageApp(root)
    root.mainloop()