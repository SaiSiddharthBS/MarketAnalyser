from PIL import Image

img = Image.open("Agent Alpha Logo v2.png").convert("RGB")
w, h = img.size

# Find bounding box of pixels that are not black
# We can use Image.point to threshold the image, then getbbox
threshold = 15
mask = img.point(lambda p: 255 if p > threshold else 0).convert("1")
bbox = mask.getbbox()

print(f"Original size: {w}x{h}")
print(f"Bounding box (> {threshold}): {bbox}")

# Calculate margins
left, upper, right, lower = bbox
print(f"Margins: left={left}, top={upper}, right={w-right}, bottom={h-lower}")

