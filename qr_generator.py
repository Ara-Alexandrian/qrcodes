#!/usr/bin/env python
import os
import numpy as np
import cv2
import qrcode
from PIL import Image

def generate_qr_code(url, size=300):
    """Generate a QR code for the given URL"""
    qr = qrcode.QRCode(
        version=4,  
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Highest error correction
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))
    # Convert to numpy array and ensure it's uint8
    np_img = np.array(img).astype(np.uint8) * 255
    return np_img

def extract_flame_mask(logo_path):
    """Extract the mask of the red flame from the logo"""
    try:
        # Read the logo image
        logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)

        if logo is None:
            print(f"Failed to load logo from {logo_path}")
            # Return a blank mask and image if logo failed to load
            return np.zeros((100, 100), dtype=np.uint8), np.zeros((100, 100, 3), dtype=np.uint8)

        # Check image dimensions and channels
        if len(logo.shape) < 2:
            print(f"Invalid logo format: {logo.shape}")
            return np.zeros((100, 100), dtype=np.uint8), np.zeros((100, 100, 3), dtype=np.uint8)

        # Handle grayscale images (2D)
        if len(logo.shape) == 2:
            # Convert grayscale to BGR
            logo = cv2.cvtColor(logo, cv2.COLOR_GRAY2BGR)
            # Create a binary mask based on non-white pixels
            alpha = np.all(logo > 240, axis=2).astype(np.uint8)
            alpha = 1 - alpha  # Invert to have 1 for logo, 0 for background
        # Handle images with alpha (4 channels)
        elif logo.shape[2] == 4:
            # Extract alpha channel if present
            alpha = logo[:, :, 3]
            logo = cv2.cvtColor(logo, cv2.COLOR_BGRA2BGR)
        # Handle regular BGR images (3 channels)
        else:
            # Create a binary mask based on non-white pixels
            alpha = np.all(logo > 240, axis=2).astype(np.uint8)
            alpha = 1 - alpha  # Invert to have 1 for logo, 0 for background

        # Extract red channel and create a mask for the red flame
        hsv = cv2.cvtColor(logo, cv2.COLOR_BGR2HSV)

        # Define range for red color in HSV - wider range to capture all reds
        lower_red1 = np.array([0, 30, 30])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([150, 30, 30])
        upper_red2 = np.array([180, 255, 255])

        # Create masks for red regions
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

        # Combine the red masks
        red_mask = cv2.bitwise_or(mask1, mask2)

        # Apply the alpha channel if available
        if 'alpha' in locals():
            red_mask = cv2.bitwise_and(red_mask, alpha * 255)

        # For the specific logo, use the entire non-white area as the flame
        # since we know it's just the flame shape
        if np.sum(red_mask) < 100:  # If red detection failed
            gray = cv2.cvtColor(logo, cv2.COLOR_BGR2GRAY)
            _, red_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

        return red_mask, logo

    except Exception as e:
        print(f"Error extracting flame mask: {e}")
        # Return blank placeholder on error
        return np.zeros((100, 100), dtype=np.uint8), np.zeros((100, 100, 3), dtype=np.uint8)

def create_qr_in_flame(logo_path, url, output_path, manufacturer="", model="", serial=""):
    """Create a QR code that integrates with the logo while maintaining full functionality

    Args:
        logo_path: Path to the Mary Bird Perkins logo
        url: URL to encode in the QR code
        output_path: Path where the QR code will be saved
        manufacturer: Equipment manufacturer to display on left side
        model: Model number to display on right side
        serial: Serial number to display on right side
    """
    try:
        print(f"Creating QR code with flame logo from: {logo_path}")
        print(f"URL: {url}")
        print(f"Output path: {output_path}")

        # Create dimensions - optimize for label maker (more compact)
        final_size = 800  # Slightly smaller final image
        qr_size = 600     # Keep QR code size the same for scannability

        # Fixed logo size for uniform appearance
        logo_size_percent = 70

        # COMPLETE REWRITE APPROACH:
        # Create a fresh canvas and draw only what we want without any artifacts

        # Step 1: Load and prepare the logo and flame
        print("Extracting flame mask...")
        flame_mask, logo_bgr = extract_flame_mask(logo_path)

        # Get dimensions
        height, width = flame_mask.shape[:2]
        print(f"Flame mask dimensions: {width}x{height}")

        # Step 2: Create the QR code
        print("Generating QR code...")
        qr_image = generate_qr_code(url, size=qr_size)
        qr_black_mask = (qr_image < 128).astype(np.uint8)

        # Step 3: Create a pristine white background image
        result = np.ones((final_size, final_size, 3), dtype=np.uint8) * 255

        # Set the flame color - darker red to match NEW-SAMPLE.png
        flame_color = (20, 20, 200)  # BGR for deeper red color

        # Calculate center and QR code position
        center = (final_size // 2, final_size // 2)
        qr_pos_x = center[0] - qr_size // 2
        qr_pos_y = center[1] - qr_size // 2

        # Define QR boundaries
        qr_top = qr_pos_y
        qr_bottom = qr_pos_y + qr_size
        qr_left = qr_pos_x
        qr_right = qr_pos_x + qr_size

        # Step 4: Resize the flame to proper size
        flame_size = int(qr_size * (logo_size_percent/100))
        scale = flame_size / max(height, width)
        new_logo_height = int(height * scale)
        new_logo_width = int(width * scale)

        print(f"Resizing flame to {new_logo_width}x{new_logo_height}")

        # Resize flame mask
        flame_mask_resized = cv2.resize(flame_mask, (new_logo_width, new_logo_height))

        # Step 5: Place the flame in the center
        logo_pos_x = center[0] - new_logo_width // 2
        logo_pos_y = center[1] - new_logo_height // 2

        print(f"Placing flame at position: {logo_pos_x},{logo_pos_y}")

        # Apply flame with semi-transparency
        print("Applying flame overlay...")
        for y in range(new_logo_height):
            for x in range(new_logo_width):
                if (logo_pos_y + y < final_size and logo_pos_x + x < final_size):
                    if flame_mask_resized[y, x] > 0:
                        opacity = 0.7
                        flame_alpha = flame_mask_resized[y, x] / 255.0 * opacity
                        current_pixel = result[logo_pos_y + y, logo_pos_x + x].astype(float)
                        blended = current_pixel * (1 - flame_alpha) + np.array(flame_color) * flame_alpha
                        result[logo_pos_y + y, logo_pos_x + x] = blended.astype(np.uint8)

        # Step 6: Overlay QR code on top
        print("Adding QR code...")
        for y in range(qr_size):
            for x in range(qr_size):
                if qr_pos_y + y < final_size and qr_pos_x + x < final_size:
                    if qr_black_mask[y, x] == 1:  # Black QR module
                        result[qr_pos_y + y, qr_pos_x + x] = [0, 0, 0]  # Black

        # Step 8: Add the perimeter text as a design element
        print("Adding text...")
        # Define Mary Bird Perkins flame color (BGR format) - matching the flame color
        flame_color = (31, 44, 177)  # Red flame color in BGR (same as used for the flame)

        # Set header font and size - use a more elegant font
        header_font = cv2.FONT_HERSHEY_SIMPLEX  # Base font
        header_font_scale = 1.0
        header_font_thickness = 2

        # Side text font - smaller
        side_font = cv2.FONT_HERSHEY_SIMPLEX
        side_font_scale = 0.7
        side_font_thickness = 1

        # Draw "Property of Mary Bird Perkins Cancer Center" at the top (two lines)
        top_text1 = "Property of"
        top_text2 = "Mary Bird Perkins Cancer Center"

        # First line - bring closer to QR code
        top_text1_size = cv2.getTextSize(top_text1, header_font, header_font_scale, header_font_thickness)[0]
        top_text1_position = (center[0] - top_text1_size[0] // 2, qr_top - 40)  # Closer to QR
        cv2.putText(result, top_text1, top_text1_position, header_font, header_font_scale, flame_color, header_font_thickness)

        # Second line - bring closer to QR code
        top_text2_size = cv2.getTextSize(top_text2, header_font, header_font_scale, header_font_thickness)[0]
        top_text2_position = (center[0] - top_text2_size[0] // 2, qr_top - 10)  # Very close to QR
        cv2.putText(result, top_text2, top_text2_position, header_font, header_font_scale, flame_color, header_font_thickness)

        # Draw "Department of Medical Physics" at the bottom - closer to QR
        bottom_text = "Department of Medical Physics"
        bottom_text_size = cv2.getTextSize(bottom_text, header_font, header_font_scale, header_font_thickness)[0]
        bottom_text_position = (center[0] - bottom_text_size[0] // 2, qr_bottom + 30)  # Much closer to QR
        cv2.putText(result, bottom_text, bottom_text_position, header_font, header_font_scale, flame_color, header_font_thickness)

        # Rotated text for side labels
        def draw_vertical_text(img, text, position, is_left_side=True, font=cv2.FONT_HERSHEY_SIMPLEX,
                            font_scale=0.7, color=(20, 20, 200), thickness=2):
            """Draw properly rotated text matching the NEW-SAMPLE.png

            Args:
                img: The image to draw on
                text: Text to draw
                position: (x, y) position for the center of the text
                is_left_side: If True, draw on left (90° rotation), otherwise right (-90° rotation)
                font, font_scale, color, thickness: Text styling parameters
            """
            try:
                x_pos, y_center = position

                # Check that we have valid text
                if not text:
                    return

                # Create an image for the text
                text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

                # Check that text size is valid
                if text_size[0] <= 0 or text_size[1] <= 0:
                    print(f"Invalid text size: {text_size} for text: {text}")
                    return

                text_img_width = text_size[0] + 40  # Add padding
                text_img_height = text_size[1] + 40

                # Create blank canvas for the text (white background)
                text_img = np.ones((text_img_height, text_img_width, 3), dtype=np.uint8) * 255

                # Draw the text centered on this canvas
                text_x = (text_img_width - text_size[0]) // 2
                text_y = (text_img_height + text_size[1]) // 2
                cv2.putText(text_img, text, (text_x, text_y), font, font_scale, color, thickness)

                # Set rotation angle based on side
                if is_left_side:
                    # Left side: rotate 90 degrees counter-clockwise
                    angle = 90
                else:
                    # Right side: rotate 90 degrees clockwise
                    angle = -90

                # Rotate the image
                rotation_matrix = cv2.getRotationMatrix2D(
                    (text_img_width // 2, text_img_height // 2), angle, 1)

                # Calculate new dimensions after rotation
                cosine = abs(rotation_matrix[0, 0])
                sine = abs(rotation_matrix[0, 1])
                new_w = int((text_img_height * sine) + (text_img_width * cosine))
                new_h = int((text_img_height * cosine) + (text_img_width * sine))

                # Adjust the rotation matrix
                rotation_matrix[0, 2] += (new_w / 2) - (text_img_width // 2)
                rotation_matrix[1, 2] += (new_h / 2) - (text_img_height // 2)

                # Perform the rotation
                rotated_text = cv2.warpAffine(text_img, rotation_matrix, (new_w, new_h),
                                            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                            borderValue=(255, 255, 255))

                # Calculate position to place the rotated text
                x_start = x_pos - rotated_text.shape[1] // 2
                y_start = y_center - rotated_text.shape[0] // 2

                # Paste the rotated text onto the result image
                # Only copy non-white pixels (text only)
                for y in range(rotated_text.shape[0]):
                    for x in range(rotated_text.shape[1]):
                        if 0 <= y_start + y < img.shape[0] and 0 <= x_start + x < img.shape[1]:
                            pixel = rotated_text[y, x]
                            # Only copy text pixels (not white background)
                            if not np.all(pixel > 250):
                                img[y_start + y, x_start + x] = pixel
            except Exception as e:
                print(f"Error drawing vertical text: {e}")

        # Draw side text with proper rotation, closer to QR code for label maker
        side_margin = 40  # Reduced margin to bring text closer to QR

        # Left side text (MFR: IBA) - rotate 90 degrees (reads bottom to top)
        if manufacturer:
            print(f"Adding manufacturer: {manufacturer}")
            # Format matches NEW-SAMPLE.png
            left_text = f"MFR: {manufacturer.upper()}"
            # Position on the left side of the QR code
            left_x = qr_left - side_margin
            left_y = qr_top + qr_size // 2

            # Draw rotated text (90 degrees counter-clockwise)
            draw_vertical_text(result, left_text, (left_x, left_y), is_left_side=True,
                            font_scale=0.7, thickness=2)

        # Right side combines model and serial on separate lines
        if model or serial:
            # Position for right side text
            right_x = qr_right + side_margin

            # Always display Model and Serial on separate lines like in the NEW-SAMPLE.png
            if model:
                print(f"Adding model: {model}")
                # Format the model text
                model_text = f"Model: {model.upper()}"
                # Position in upper part of QR
                model_y = qr_top + qr_size // 3
                # Draw model info separately
                draw_vertical_text(result, model_text, (right_x, model_y),
                                is_left_side=False, font_scale=0.7, thickness=2)

            if serial:
                print(f"Adding serial: {serial}")
                # Format the serial text
                serial_text = f"Serial: {serial.upper()}"
                # Position in lower part of QR (clearly separated from model)
                serial_y = qr_top + qr_size * 2 // 3
                # Draw serial info separately
                draw_vertical_text(result, serial_text, (right_x, serial_y),
                                is_left_side=False, font_scale=0.7, thickness=2)

            # If there's only one (model or serial), it will be displayed at its respective position

        # Step 9: Final polish - specifically check for and remove any horizontal lines
        print("Cleaning up final image...")
        # Check the area to the left of the QR code for any remaining horizontal lines
        # Horizontal lines might appear around the y=360 mark
        for y in range(result.shape[0]):
            # Skip area with QR code
            if qr_top <= y <= qr_bottom:
                continue

            # Check the left margin
            for x in range(0, qr_left):
                # If pixel is colored but not the flame red color of our text
                pixel = result[y, x]
                is_text_color = (pixel[0] < 150 and pixel[1] < 150 and pixel[2] > 150)

                if not np.all(pixel == [255, 255, 255]) and not is_text_color:
                    # Remove any non-text pixels to clean up potential artifacts
                    result[y, x] = [255, 255, 255]

        # Step 10: Save the result
        print(f"Saving final QR code to: {output_path}")
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, result)

        print("QR code creation complete!")
        return output_path

    except Exception as e:
        print(f"Error creating QR code with flame: {e}")
        raise Exception(f"Failed to create QR code: {e}")

def main():
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(script_dir, 'Resources', 'Mary Bird Perkins Cancer Center.png')
    output_dir = os.path.join(script_dir, 'Generated_QR')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Example URL (use default for testing or allow user input)
    try:
        url = input("Enter the URL for the QR code (or press Enter for default): ")
        if not url:
            url = "https://www.marybird.org"
    except EOFError:
        url = "https://www.marybird.org"
        print(f"Using default URL: {url}")
    
    # Prompt for manufacturer
    try:
        manufacturer = input("Enter manufacturer (or press Enter to skip): ")
    except EOFError:
        manufacturer = ""
        print("No manufacturer specified")
    
    # Prompt for model
    try:
        model = input("Enter model (or press Enter to skip): ")
    except EOFError:
        model = ""
        print("No model specified")
    
    # Prompt for serial number
    try:
        serial = input("Enter serial number (or press Enter to skip): ")
    except EOFError:
        serial = ""
        print("No serial number specified")
    
    # Create output path
    output_path = os.path.join(output_dir, f'qr_in_flame_{hash(url) % 10000}.png')
    
    # Generate the QR code inside the flame
    created_file = create_qr_in_flame(logo_path, url, output_path, manufacturer, model, serial)
    
    print(f"QR code generated successfully at: {created_file}")

if __name__ == "__main__":
    main()