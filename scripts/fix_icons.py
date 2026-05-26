from PIL import Image
import os

source_file = "Agent Alpha Logo v2.png"
output_dir = "frontend/images"

img = Image.open(source_file)

# If image has alpha channel, paste it over a black background
if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
    alpha = img.convert('RGBA').split()[-1]
    bg = Image.new("RGB", img.size, (0, 0, 0)) # pure black background
    bg.paste(img, mask=alpha)
    img = bg
else:
    img = img.convert("RGB")

sizes = {
    "apple-touch-icon-v2.png": (180, 180),
    "icon-192-v2.png": (192, 192),
    "icon-512-v2.png": (512, 512),
    "favicon-32-v2.png": (32, 32),
    "favicon-16-v2.png": (16, 16)
}

for filename, size in sizes.items():
    resized = img.resize(size, Image.Resampling.LANCZOS)
    resized.save(os.path.join(output_dir, filename), format="PNG")
    print(f"Fixed and generated {filename} at {size}")

print("All icons generated without alpha channel.")
