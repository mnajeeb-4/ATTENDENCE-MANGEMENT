import cv2
import base64
import numpy as np
import face_recognition
from pyzbar.pyzbar import decode
from PIL import Image
import io

# Note: In production, encode faces and store them as base64 strings in the DB.
# This function simulates encoding and decoding for the demo.
def encode_face(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = np.array(img)
        face_encodings = face_recognition.face_encodings(img)
        if len(face_encodings) > 0:
            # Convert numpy array to list then to string for storage
            encoding = face_encodings[0].tolist()
            return base64.b64encode(str(encoding).encode()).decode()
    except Exception as e:
        return None
    return None

def verify_face(stored_encoding_b64, image_bytes):
    if not stored_encoding_b64:
        return False
    try:
        # Decode stored
        stored_str = base64.b64decode(stored_encoding_b64).decode()
        stored_list = eval(stored_str) # Careful with eval in prod, use json
        stored_encoding = np.array(stored_list)

        # Decode input
        img = Image.open(io.BytesIO(image_bytes))
        img = np.array(img)
        face_encodings = face_recognition.face_encodings(img)
        if len(face_encodings) == 0:
            return False
        matches = face_recognition.compare_faces([stored_encoding], face_encodings[0], tolerance=0.6)
        return matches[0]
    except Exception:
        return False

def scan_qr_code(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    img = np.array(img)
    decoded_objects = decode(img)
    for obj in decoded_objects:
        return obj.data.decode('utf-8')
    return None
