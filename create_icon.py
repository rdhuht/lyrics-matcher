"""Generate application icon."""
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle with gradient
    for i in range(size // 2):
        color = (66, 133, 244, 255 - i * 3)  # Blue gradient
        draw.ellipse(
            [i, i, size - i - 1, size - i - 1],
            outline=color,
            fill=None
        )

    # Inner circle
    draw.ellipse([32, 32, size - 32, size - 32], fill=(66, 133, 244, 255))

    # Music note symbol (simplified)
    draw.ellipse([85, 140, 125, 180], fill=(255, 255, 255, 255))  # Note head
    draw.rectangle([110, 60, 120, 140], fill=(255, 255, 255, 255))  # Stem
    draw.polygon([(120, 60), (140, 80), (120, 100)], fill=(255, 255, 255, 255))  # Flag

    # Second note
    draw.ellipse([145, 120, 185, 160], fill=(255, 255, 255, 255))
    draw.rectangle([170, 50, 180, 120], fill=(255, 255, 255, 255))
    draw.polygon([(180, 50), (200, 70), (180, 90)], fill=(255, 255, 255, 255))

    # L letter for Lyrics
    draw.rectangle([200, 100, 215, 180], fill=(255, 215, 0, 255))  # Vertical
    draw.rectangle([200, 165, 230, 180], fill=(255, 215, 0, 255))  # Horizontal

    return img

def save_icon():
    img = create_icon()

    # Save as PNG
    img.save('imgs/logo.png', 'PNG')

    # Save as ICO (multiple sizes)
    img.save('imgs/logo.ico', format='ICO')
    print("Icon created: imgs/logo.png, imgs/logo.ico")

if __name__ == '__main__':
    from PIL import Image
    save_icon()