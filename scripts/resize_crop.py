from PIL import Image
import os

source_file = "Agent Alpha Logo v2.png"
output_dir = "frontend/images"

img = Image.open(source_file).convert("RGBA")

# Get bounding box of non-transparent pixels
bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)

# Now, the image has no transparent borders.
# We also want to make sure the background is black just in case there's slight transparency in the corners,
# but if we scale it up, macOS will crop the corners anyway.
bg = Image.new("RGB", img.size, (0, 0, 0))
bg.paste(img, mask=img.split()[3])
img = bg

sizes = {
    "apple-touch-icon-v4.png": (180, 180),
    "icon-192-v4.png": (192, 192),
    "icon-512-v4.png": (512, 512),
    "favicon-32-v4.png": (32, 32),
    "favicon-16-v4.png": (16, 16)
}

for filename, size in sizes.items():
    # We want to fill the canvas, so we can just resize the cropped image directly
    resized = img.resize(size, Image.Resampling.LANCZOS)
    resized.save(os.path.join(output_dir, filename), format="PNG")
    print(f"Cropped, fixed, and generated {filename} at {size}")

