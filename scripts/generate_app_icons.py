"""
Generate production icons for Tauri 2 desktop shell from approved character asset.
"""
import os
from PIL import Image

def generate_icons():
    src_path = os.path.join("public", "idle.png")
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source artwork {src_path} not found")

    out_dir = os.path.join("src-tauri", "icons")
    os.makedirs(out_dir, exist_ok=True)

    img = Image.open(src_path).convert("RGBA")

    # 1. 32x32.png
    img_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
    img_32.save(os.path.join(out_dir, "32x32.png"), "PNG")

    # 2. 128x128.png
    img_128 = img.resize((128, 128), Image.Resampling.LANCZOS)
    img_128.save(os.path.join(out_dir, "128x128.png"), "PNG")

    # 3. 128x128@2x.png (256x256)
    img_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    img_256.save(os.path.join(out_dir, "128x128@2x.png"), "PNG")

    # 4. icon.png (512x512)
    img_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    img_512.save(os.path.join(out_dir, "icon.png"), "PNG")

    # 5. icon.ico (Multi-size standard Windows icon)
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(
        os.path.join(out_dir, "icon.ico"),
        format="ICO",
        sizes=ico_sizes
    )

    # 6. tray icon (tray-32.png / tray.ico)
    img_32.save(os.path.join(out_dir, "tray.png"), "PNG")
    img_32.save(os.path.join(out_dir, "tray.ico"), format="ICO", sizes=[(16, 16), (32, 32)])

    print(f"Generated production icons in {out_dir}:")
    for f in os.listdir(out_dir):
        print(f" - {f}")

if __name__ == "__main__":
    generate_icons()
