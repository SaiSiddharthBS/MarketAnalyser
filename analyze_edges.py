from PIL import Image

img = Image.open("Agent Alpha Logo v2.png").convert("RGB")
w, h = img.size

# Sample corners and edges
samples = [
    img.getpixel((0, 0)),
    img.getpixel((w-1, 0)),
    img.getpixel((0, h-1)),
    img.getpixel((w-1, h-1)),
    img.getpixel((w//2, 0)),
    img.getpixel((0, h//2))
]
print("Edge colors:", samples)
