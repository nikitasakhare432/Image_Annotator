import cv2
import os
import json

# -----------------------------
# Folder paths
# -----------------------------
IMAGE_FOLDER = "images"
ANNOTATION_FOLDER = "annotations"

os.makedirs(ANNOTATION_FOLDER, exist_ok=True)

# Supported image extensions
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

# -----------------------------
# Global variables
# -----------------------------
drawing = False
start_x, start_y = -1, -1
current_image = None
display_image = None
annotations = []
current_box = None
current_image_name = ""


def draw_existing_annotations():
    """
    Draw all saved annotations on a fresh copy of the image.
    """
    global display_image

    display_image = current_image.copy()

    for ann in annotations:
        x1, y1, x2, y2 = ann["x1"], ann["y1"], ann["x2"], ann["y2"]
        label = ann["label"]

        cv2.rectangle(display_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Label background
        text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        text_w, text_h = text_size
        cv2.rectangle(
            display_image,
            (x1, max(0, y1 - text_h - 10)),
            (x1 + text_w + 8, y1),
            (0, 255, 0),
            -1
        )

        # Label text
        cv2.putText(
            display_image,
            label,
            (x1 + 4, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2
        )

    # Instructions
    cv2.putText(
        display_image,
        "Draw box: mouse drag | s=save | u=undo | n=next | q=quit",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 0, 0),
        2
    )


def mouse_draw(event, x, y, flags, param):
    """
    Mouse callback for drawing bounding boxes.
    """
    global drawing, start_x, start_y, display_image, current_box

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_x, start_y = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            temp_image = display_image.copy()
            cv2.rectangle(temp_image, (start_x, start_y), (x, y), (0, 0, 255), 2)
            cv2.imshow("Image Annotation Tool", temp_image)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False

        x1 = min(start_x, x)
        y1 = min(start_y, y)
        x2 = max(start_x, x)
        y2 = max(start_y, y)

        # Ignore too-small boxes
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            print("Box too small, ignored.")
            draw_existing_annotations()
            cv2.imshow("Image Annotation Tool", display_image)
            return

        label = input("Enter label for selected box: ").strip()

        if not label:
            print("Empty label not allowed. Box discarded.")
            draw_existing_annotations()
            cv2.imshow("Image Annotation Tool", display_image)
            return

        current_box = {
            "label": label,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        }

        annotations.append(current_box)
        print(f"Added annotation: {current_box}")

        draw_existing_annotations()
        cv2.imshow("Image Annotation Tool", display_image)


def save_annotations(image_name):
    """
    Save annotations to a JSON file with the same image name.
    """
    annotation_file = os.path.join(
        ANNOTATION_FOLDER,
        os.path.splitext(image_name)[0] + ".json"
    )

    output_data = {
        "image": image_name,
        "annotations": annotations
    }

    with open(annotation_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)

    print(f"Annotations saved to: {annotation_file}")


def load_images():
    """
    Load all valid images from IMAGE_FOLDER.
    """
    if not os.path.exists(IMAGE_FOLDER):
        print(f"Folder '{IMAGE_FOLDER}' does not exist.")
        return []

    files = sorted([
        f for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith(VALID_EXTENSIONS)
    ])

    return files


def annotate_images():
    """
    Main function to annotate images one by one.
    """
    global current_image, display_image, annotations, current_image_name

    image_files = load_images()

    if not image_files:
        print("No images found in 'images' folder.")
        return

    cv2.namedWindow("Image Annotation Tool")
    cv2.setMouseCallback("Image Annotation Tool", mouse_draw)

    for image_name in image_files:
        image_path = os.path.join(IMAGE_FOLDER, image_name)
        current_image = cv2.imread(image_path)

        if current_image is None:
            print(f"Could not load image: {image_name}")
            continue

        current_image_name = image_name
        annotations = []

        draw_existing_annotations()

        while True:
            cv2.imshow("Image Annotation Tool", display_image)
            key = cv2.waitKey(1) & 0xFF

            # Save
            if key == ord('s'):
                save_annotations(image_name)

            # Undo
            elif key == ord('u'):
                if annotations:
                    removed = annotations.pop()
                    print(f"Removed last annotation: {removed}")
                    draw_existing_annotations()
                else:
                    print("No annotations to undo.")

            # Next image
            elif key == ord('n'):
                print(f"Moving to next image: {image_name}")
                break

            # Quit
            elif key == ord('q'):
                choice = input("Do you want to save before quitting? (y/n): ").strip().lower()
                if choice == 'y':
                    save_annotations(image_name)
                cv2.destroyAllWindows()
                print("Exited annotation tool.")
                return

    cv2.destroyAllWindows()
    print("All images completed.")


if __name__ == "__main__":
    annotate_images()