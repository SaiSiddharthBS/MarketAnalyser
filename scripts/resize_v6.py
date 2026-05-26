from PIL import Image
import os
import numpy as np

source_file = "Agent Alpha Logo v2.png"
output_dir = "frontend/images"

# 1. Load and do the v4 crop
img = Image.open(source_file).convert("RGB")
w, h = img.size
crop_amount = int(w * 0.18)
base_img = img.crop((crop_amount, crop_amount, w - crop_amount, h - crop_amount))

# 2. To make the logo smaller but keep the background reaching the edges,
# we scale the base_img down to 85%, and extend the edge pixels to fill the rest.
scale_factor = 0.85
new_w = int(base_img.width * scale_factor)
new_h = int(base_img.height * scale_factor)

scaled_img = base_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

# Create a blank canvas of the original base_img size
final_img = Image.new("RGB", base_img.size)

# Paste scaled image in center
pad_x = (base_img.width - new_w) // 2
pad_y = (base_img.height - new_h) // 2
final_img.paste(scaled_img, (pad_x, pad_y))

# Convert to numpy to stretch edges
arr = np.array(final_img)

# Stretch top
for y in range(pad_y):
    arr[y, pad_x:pad_x+new_w] = arr[pad_y, pad_x:pad_x+new_w]
# Stretch bottom
for y in range(pad_y + new_h, base_img.height):
    arr[y, pad_x:pad_x+new_w] = arr[pad_y + new_h - 1, pad_x:pad_x+new_w]
# Stretch left
for x in range(pad_x):
    arr[:, x] = arr[:, pad_x]
# Stretch right
for x in range(pad_x + new_w, base_img.width):
    arr[:, x] = arr[:, pad_x + new_w - 1]

# Corner fills
# Top-Left
arr[:pad_y, :pad_x] = arr[pad_y, pad_x]
# Top-Right
arr[:pad_y, pad_x+new_w:] = arr[pad_y, pad_x+new_w-1]
# Bottom-Left
arr[pad_y+new_h:, :pad_x] = arr[pad_y+new_h-1, pad_x]
# Bottom-Right
arr[pad_y+new_h:, pad_x+new_w:] = arr[pad_y+new_h-1, pad_x+new_w-1]

final_img = Image.fromarray(arr)

sizes = {
    "apple-touch-icon-v6.png": (180, 180),
    "icon-192-v6.png": (192, 192),
    "icon-512-v6.png": (512, 512),
    "favicon-32-v6.png": (32, 32),
    "favicon-16-v6.png": (16, 16)
}

for filename, size in sizes.items():
    resized = final_img.resize(size, Image.Resampling.LANCZOS)
    resized.save(os.path.join(output_dir, filename), format="PNG")
    print(f"Generated {filename} at {size}")

