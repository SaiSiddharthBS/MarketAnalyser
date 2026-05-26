from PIL import Image
import os

source_file = "Agent Alpha Logo v2.png"
output_dir = "frontend/images"

img = Image.open(source_file).convert("RGB")
w, h = img.size

# Zoom in by 20% to crop out the baked-in borders and background
crop_amount = int(w * 0.18)
bbox = (crop_amount, crop_amount, w - crop_amount, h - crop_amount)
img = img.crop(bbox)

sizes = {
    "apple-touch-icon-v5.png": (180, 180),
    "icon-192-v5.png": (192, 192),
    "icon-512-v5.png": (512, 512),
    "favicon-32-v5.png": (32, 32),
    "favicon-16-v5.png": (16, 16)
}

for filename, size in sizes.items():
    resized = img.resize(size, Image.Resampling.LANCZOS)
    resized.save(os.path.join(output_dir, filename), format="PNG")
    print(f"Zoomed and generated {filename} at {size}")

