import os
import random
import math
from PIL import Image
import glob


def process_batch_randomly_balanced(image_paths, output_folder):
    """
    Takes a list of images. Assigns a specific role (Top, Center, or Bottom)
    to each image such that the total count of roles is balanced.
    Saves the specific crop to the output folder.
    """

    # 1. Setup Output Directory
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created folder: {output_folder}")

    # 2. Create the "Deck" of assignments to ensure balance
    num_images = len(image_paths)
    if num_images == 0:
        print("No images provided.")
        return

    # Calculate how many of each we need (e.g., 15 images -> 5 of each)
    base_count = num_images // 3
    remainder = num_images % 3

    # Create the pool: ['top', 'top'..., 'center', 'center'..., 'bottom', 'bottom'...]
    assignments = []
    assignments.extend(['top'] * base_count)
    assignments.extend(['center'] * base_count)
    assignments.extend(['bottom'] * base_count)

    # Handle remainders randomly if total isn't divisible by 3
    remainder_choices = ['top', 'center', 'bottom']
    # Shuffle choices to pick random extras
    random.shuffle(remainder_choices)
    for i in range(remainder):
        assignments.append(remainder_choices[i])

    # 3. Shuffle the assignments
    # This ensures Image 1 doesn't always get 'top'.
    # The distribution remains balanced, but the order is random.
    random.shuffle(assignments)

    # Counters for naming files (top_1, top_2, etc.)
    counters = {
        'top': 1,
        'center': 1,
        'bottom': 1
    }

    print(f"Processing {num_images} images with balanced distribution...")
    print(
        f"Target: {assignments.count('top')} Tops, {assignments.count('center')} Centers, {assignments.count('bottom')} Bottoms.\n")

    # 4. Process each image according to its assigned role
    for i, img_path in enumerate(image_paths):
        role = assignments[i]

        if not os.path.exists(img_path):
            print(f"Skipping missing file: {img_path}")
            continue

        try:
            with Image.open(img_path) as img:
                width, height = img.size

                # Calculate slice height
                slice_height = height // 3

                # Define crop box (left, top, right, bottom)
                if role == 'top':
                    crop_box = (0, 0, width, slice_height)
                elif role == 'center':
                    crop_box = (0, slice_height, width, slice_height * 2)
                elif role == 'bottom':
                    # Go to the very edge to handle rounding errors
                    crop_box = (0, slice_height * 2, width, height)

                # Crop
                cropped_img = img.crop(crop_box)

                # Generate Output Filename
                # Get original extension or default to .jpg
                _, ext = os.path.splitext(img_path)
                if not ext: ext = ".jpg"

                # Naming: role + counter (e.g., top_1.jpg)
                new_filename = f"{role}_{counters[role]}{ext}"
                save_path = os.path.join(output_folder, new_filename)

                cropped_img.save(save_path)

                # Increment counter for that specific role
                counters[role] += 1

                print(
                    f"[{i + 1}/{num_images}] '{os.path.basename(img_path)}' -> assigned '{role}' -> Saved as {new_filename}")

        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    print("\nDone! Images saved.")


# --- Usage Example ---
if __name__ == "__main__":

    # 1. Define Output Path
    out_dir = "./static/imgout"

    # 2. Define Input (Simulating an array of files)
    # In a real scenario, you might use: glob.glob("folder/*.jpg")

    # Let's create dummy files for demonstration so you can run this immediately
    input_files_list = glob.glob("static/celebrity_whole/*.png")
    #print(f"Input files: {input_files_list}")


    process_batch_randomly_balanced(input_files_list, out_dir)

