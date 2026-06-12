"""Generate application icon with multiple sizes for ICO."""
from PIL import Image, ImageDraw
import struct
import io

def create_icon():
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle with gradient
    for i in range(size // 2):
        alpha = max(0, 255 - i * 3)
        color = (66, 133, 244, alpha)
        draw.ellipse([i, i, size - i - 1, size - i - 1], outline=color)

    # Inner circle
    draw.ellipse([32, 32, size - 32, size - 32], fill=(66, 133, 244, 255))

    # Music notes
    draw.ellipse([80, 145, 125, 185], fill=(255, 255, 255, 255))
    draw.rectangle([110, 55, 120, 145], fill=(255, 255, 255, 255))
    draw.polygon([(120, 55), (145, 75), (120, 95)], fill=(255, 255, 255, 255))

    draw.ellipse([145, 125, 190, 165], fill=(255, 255, 255, 255))
    draw.rectangle([175, 45, 185, 125], fill=(255, 255, 255, 255))
    draw.polygon([(185, 45), (210, 65), (185, 85)], fill=(255, 255, 255, 255))

    # L for Lyrics
    draw.rectangle([200, 100, 215, 185], fill=(255, 215, 0, 255))
    draw.rectangle([200, 168, 232, 185], fill=(255, 215, 0, 255))

    return img

def save_icon():
    img = create_icon()

    # Save PNG
    img.save('imgs/logo.png', 'PNG')

    # Create ICO with multiple sizes using proper ICO format
    sizes = [256, 128, 64, 48, 32, 16]
    images = []

    for s in sizes:
        images.append(img.resize((s, s), Image.Resampling.LANCZOS).convert('RGBA'))

    # Save largest as ICO (Windows will handle it)
    images[0].save('imgs/logo.ico', format='ICO')
    print("Icon created: imgs/logo.png, imgs/logo.ico")

if __name__ == '__main__':
    save_icon()