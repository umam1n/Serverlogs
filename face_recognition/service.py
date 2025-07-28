import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from deepface import DeepFace

# Create a directory to store face embeddings
DB_PATH = os.path.join(os.getcwd(), "face_db")
os.makedirs(DB_PATH, exist_ok=True)

app = FastAPI()

def read_imagefile(file) -> np.ndarray:
    """Reads an uploaded image file and returns it as a NumPy array."""
    contents = np.fromstring(file, np.uint8)
    img = cv2.imdecode(contents, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")
    return img

@app.post("/enroll/{user_id}")
async def enroll_user(user_id: str, file: UploadFile = File(...)):
    """Enrolls a user by saving their face representation."""
    image = read_imagefile(await file.read())
    try:
        # You can add a check here to ensure a face is detected
        _ = DeepFace.represent(img_path=image, enforce_detection=True, model_name='Facenet512')

        user_dir = os.path.join(DB_PATH, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        # --- FIX THIS LINE ---
        # Use the filename sent from the Django app (e.g., "front.png")
        file_path = os.path.join(user_dir, file.filename)
        # ---------------------

        cv2.imwrite(file_path, image)
        return {"status": "success", "user_id": user_id, "message": f"Saved {file.filename}."}

    except ValueError as e:
        # This happens if DeepFace can't find a face
        raise HTTPException(status_code=400, detail=f"Could not process face in {file.filename}: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/recognize")
async def recognize_faces(file: UploadFile = File(...)):
    """Recognizes faces in an image against the enrolled database."""
    image = read_imagefile(await file.read())
    try:
        # DeepFace.find will search for matches in the DB_PATH directory.
        dfs = DeepFace.find(
            img_path=image,
            db_path=DB_PATH,
            enforce_detection=False, # Try to find faces even if detection is weak
            model_name='Facenet512',
            silent=True
        )
        
        recognized_ids = []
        if dfs and not dfs[0].empty:
             # The 'identity' column contains the path to the matched image.
             # We parse the user_id from this path.
            recognized_ids = dfs[0]['identity'].apply(lambda x: os.path.basename(os.path.dirname(x))).unique().tolist()
            
        return {"recognized_ids": recognized_ids}
    except Exception as e:
        print(f"Recognition crashed with error: {e}")
        raise HTTPException(status_code=500, detail=f"Recognition error: {e}")