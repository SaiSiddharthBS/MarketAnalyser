from PIL import Image, ImageEnhance
import os
import numpy as np

source_file = "Agent Alpha Logo v2.png"
output_dir = "frontend/images"

# 1. Load the original image
img = Image.open(source_file).convert("RGB")

# 2. Convert to numpy array to do a non-linear brightness boost (Levels/Curves)
# We want to boost highlights/midtones but keep shadows dark.
arr = np.array(img, dtype=np.float32)

# Normalize to 0-1
arr /= 255.0

# Apply gamma correction to brighten midtones (gamma < 1 makes it brighter)
gamma = 0.65
arr = np.power(arr, gamma)

# To ensure the deep blacks stay completely black, we can subtract a tiny amount and clip
arr = np.clip(arr - 0.02, 0, 1)

# Convert back to 0-255
arr = np.uint8(arr * 255)
bright_img = Image.fromarray(arr)

# You can also boost contrast slightly to make it pop more
enhancer = ImageEnhance.Contrast(bright_img)
bright_img = enhancer.enhance(1.2)

# --- Now run the v6 padding/scaling logic on this bright_img ---

w, h = bright_img.size
crop_amount = int(w * 0.18)
base_img = bright_img.crop((crop_amount, crop_amount, w - crop_amount, h - crop_amount))

scale_factor = 0.85
new_w = int(base_img.width * scale_factor)
new_h = int(base_img.height * scale_factor)

scaled_img = base_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
final_img = Image.new("RGB", base_img.size)

pad_x = (base_img.width - new_w) // 2
pad_y = (base_img.height - new_h) // 2
final_img.paste(scaled_img, (pad_x, pad_y))

arr_final = np.array(final_img)

# Stretch top
for y in range(pad_y):
    arr_final[y, pad_x:pad_x+new_w] = arr_final[pad_y, pad_x:pad_x+new_w]
# Stretch bottom
for y in range(pad_y + new_h, base_img.height):
    arr_final[y, pad_x:pad_x+new_w] = arr_final[pad_y + new_h - 1, pad_x:pad_x+new_w]
# Stretch left
for x in range(pad_x):
    arr_final[:, x] = arr_final[:, pad_x]
# Stretch right
for x in range(pad_x + new_w, base_img.width):
    arr_final[:, x] = arr_final[:, pad_x + new_w - 1]

# Corner fills
arr_final[:pad_y, :pad_x] = arr_final[pad_y, pad_x]
arr_final[:pad_y, pad_x+new_w:] = arr_final[pad_y, pad_x+new_w-1]
arr_final[pad_y+new_h:, :pad_x] = arr_final[pad_y+new_h-1, pad_x]
arr_final[pad_y+new_h:, pad_x+new_w:] = arr_final[pad_y+new_h-1, pad_x+new_w-1]

final_img = Image.fromarray(arr_final)

sizes = {
    "apple-touch-icon-v7.png": (180, 180),
    "icon-192-v7.png": (192, 192),
    "icon-512-v7.png": (512, 512),
    "favicon-32-v7.png": (32, 32),
    "favicon-16-v7.png": (16, 16)
}

for filename, size in sizes.items():
    resized = final_img.resize(size, Image.Resampling.LANCZOS)
    resized.save(os.path.join(output_dir, filename), format="PNG")
    print(f"Generated brightened {filename} at {size}")

