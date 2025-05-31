import os
import ghostscript
from PIL import Image

PS_FOLDER = "c:/Users/stell/OneDrive/THE LAST DANCE/code/converter/PS"
JPEG_FOLDER = "c:/Users/stell/OneDrive/THE LAST DANCE/code/converter/JPEG"


if not os.path.exists(PS_FOLDER):
    print(f"Error: PS folder '{PS_FOLDER}' does not exist.")
    exit(1)


def convert_ps_to_png(ps_file, png_file):
    """Convert a .ps file to a .png file using Ghostscript with better alignment."""
    args = [
        "ps2png",  
        "-dNOPAUSE", "-dBATCH", "-dSAFER",
        "-sDEVICE=png16m",  # Output to PNG format
        "-r300",  # Resolution 
        "-dEPSCrop",  # Crop to the bounding box of the content
        "-sOutputFile=" + png_file,  # Output path for PNG
        ps_file  # Input PS file
    ]
    try:
        ghostscript.Ghostscript(*args)
        print(f"Converted {ps_file} -> {png_file}")
    except Exception as e:
        print(f"Error converting {ps_file} to PNG: {e}")

def convert_png_to_jpeg(png_file, jpeg_file):
    """Convert a .png file to a .jpeg file using Pillow."""
    try:
        with Image.open(png_file) as img:
            img.convert("RGB").save(jpeg_file, "JPEG", quality=95) 
        print(f"Converted {png_file} -> {jpeg_file}")
    except Exception as e:
        print(f"Error converting {png_file} to JPEG: {e}")

def process_ps_files():
    """Find all .ps files in PS_FOLDER, convert them to .png and then .jpeg."""
    for filename in os.listdir(PS_FOLDER):
        if filename.lower().endswith(".ps"):
            ps_path = os.path.join(PS_FOLDER, filename)
            png_path = os.path.join(JPEG_FOLDER, filename.replace(".ps", ".png"))
            jpeg_path = os.path.join(JPEG_FOLDER, filename.replace(".ps", ".jpeg"))

            convert_ps_to_png(ps_path, png_path)

            convert_png_to_jpeg(png_path, jpeg_path)

            os.remove(png_path)

if __name__ == "__main__":
    process_ps_files()
    print("Conversion complete.")
