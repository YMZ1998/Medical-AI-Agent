#!/usr/bin/env python3
"""
Test image generator: writes images to a folder for testing serve_latest_image.py
"""

import os
import time
import argparse
from PIL import Image, ImageDraw, ImageFont
import random

def generate_image(path: str, size=(512, 512)):
    """生成一张随机颜色 + 时间戳的图片"""
    img = Image.new("RGB", size, (random.randint(0,255), random.randint(0,255), random.randint(0,255)))
    draw = ImageDraw.Draw(img)
    text = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        font = ImageFont.load_default()
    except:
        font = None
    draw.text((10,10), text, fill=(255,255,255), font=font)
    img.save(path)
    print(f"Generated: {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=r"D:\debug\test", help="Folder to save images")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between images")
    parser.add_argument("--format", choices=["png","tif"], default="png", help="Image format")
    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)

    counter = 0
    try:
        while True:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"img_{timestamp}_{counter:03d}.{args.format}"
            path = os.path.join(args.dir, filename)
            generate_image(path)
            counter += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    main()
