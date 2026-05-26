from PIL import Image
import shutil
import os

source_file = "Agent Alpha Logo v2.png"
output_dir = "frontend/images"

# Copy original
shutil.copy(source_file, os.path.join(output_dir, "logo-original.png"))

img = Image.open(source_file)

sizes = {
    "apple-touch-icon.png": (180, 180),
    "icon-192.png": (192, 192),
    "icon-512.png": (512, 512),
    "favicon-32.png": (32, 32),
    "favicon-16.png": (16, 16)
}

for filename, size in sizes.items():
    resized = img.resize(size, Image.Resampling.LANCZOS)
    resized.save(os.path.join(output_dir, filename))
    print(f"Generated {filename} at {size}")

print("All icons generated successfully.")
