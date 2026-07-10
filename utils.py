import cv2
import numpy as np

def verify_face_capture(image_bytes):
    """
    Takes image bytes from st.camera_input, decodes it, and verifies if a face is present.
    Returns a dictionary {verified: bool, message: str}.
    """
    try:
        # Convert bytes to numpy array
        np_arr = np.frombuffer(image_bytes, np.uint8)
        # Decode image
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        # Load pre-trained Haar Cascade for face detection
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            return {"verified": True, "message": "Face verified successfully!"}
        else:
            return {"verified": False, "message": "No face detected. Please try again."}
    except Exception as e:
        return {"verified": False, "message": f"Error during verification: {str(e)}"}
