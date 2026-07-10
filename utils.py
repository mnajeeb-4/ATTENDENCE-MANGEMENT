import cv2
import base64
import numpy as np
from deepface import DeepFace
from pyzbar.pyzbar import decode
from PIL import Image
import io

def encode_face(image_bytes):
    # DeepFace doesn't have a manual encoder like dlib. 
    # We rely on the model extracting a face, so we just return a "yes" flag 
    # indicating the face was detected and can be stored in the DB.
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = np.array(img)
        # Detect if a face exists
        faces = DeepFace.extract_faces(img, enforce_detection=True)
        if faces:
            # For the database, we store the bytes directly or a placeholder string 
            # since DeepFace handles verification on the fly with numpy arrays.
            return base64.b64encode(image_bytes).decode()
    except Exception as e:
        return None
    return None

def verify_face(stored_encoding_b64, image_bytes):
    if not stored_encoding_b64:
        return False
    try:
        # Decode the stored image bytes
        stored_bytes = base64.b64decode(stored_encoding_b64)
        stored_img = Image.open(io.BytesIO(stored_bytes))
        stored_array = np.array(stored_img)

        # Decode the input image
        input_img = Image.open(io.BytesIO(image_bytes))
        input_array = np.array(input_img)

        # Perform verification
        result = DeepFace.verify(
            img1_path=input_array,
            img2_path=stored_array,
            enforce_detection=False,
            model_name="VGG-Face"
        )
        return result["verified"]
    except Exception:
        return False

def scan_qr_code(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    img = np.array(img)
    decoded_objects = decode(img)
    for obj in decoded_objects:
        return obj.data.decode('utf-8')
    return None
