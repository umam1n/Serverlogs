import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from deepface import DeepFace


# Define the path to the folder where face images will be stored
DB_PATH = os.path.join(os.path.dirname(__file__), "face_db")
os.makedirs(DB_PATH, exist_ok=True)

# Initialize the FastAPI application
API_KEY = os.environ.get("FACE_API_KEY", "not-so-secret-key-am-i")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
# --- END NEW ---

app = FastAPI()

def read_imagefile(file_bytes: bytes) -> np.ndarray:
    """Reads image bytes and returns a NumPy array."""
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")
    return img


@app.post("/enroll/{user_id}", dependencies=[Depends(get_api_key)])
async def enroll_user(user_id: str, file: UploadFile = File(...)):
    """
    Enrolls a user by saving their face images.
    This is set to be forgiving and will try to process even if face detection is weak.
    """
    image = read_imagefile(await file.read())
    try:
        # We try to represent the face but don't strictly enforce detection,
        # making the initial enrollment process easier for the user.
        _ = DeepFace.represent(img_path=image, enforce_detection=False, model_name='Facenet512')
        
        user_dir = os.path.join(DB_PATH, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        # Use the filename sent from the Django app (e.g., "front.png")
        # to save multiple, unique images per user.
        file_path = os.path.join(user_dir, file.filename)
        cv2.imwrite(file_path, image)
        
        return {"status": "success", "user_id": user_id, "message": f"Saved {file.filename}."}

    except ValueError as e:
        # This can still happen if the image is completely unprocessable
        print(f"Enrollment ValueError for user {user_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Could not process face in {file.filename}: {e}")
    except Exception as e:
        print(f"Enrollment Exception for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")



@app.post("/recognize", dependencies=[Depends(get_api_key)])
async def recognize_faces(file: UploadFile = File(...)):
    """
    Recognizes a face from a check-in photo against the database of enrolled users.
    """
    image = read_imagefile(await file.read())
    try:
        # DeepFace.find searches the db_path for a match.
        dfs = DeepFace.find(
            img_path=image,
            db_path=DB_PATH,
            # MODIFIED: Set to False to be more tolerant of webcam images
            # that might be slightly blurry or at an angle.
            enforce_detection=False,
            model_name='Facenet512',
            silent=True
        )
        
        recognized_ids = []
        if dfs and not dfs[0].empty:
            # The 'identity' column contains the path to the matched image.
            # We parse the user_id from this path (e.g., ".../face_db/28/front.png" -> "28")
            recognized_ids = dfs[0]['identity'].apply(lambda x: os.path.basename(os.path.dirname(x))).unique().tolist()
            
        return {"recognized_ids": recognized_ids}
    except Exception as e:
        # This can happen if no faces are found in the check-in photo
        print(f"Recognition crashed with error: {e}")
        # Return an empty list if any error occurs
        return {"recognized_ids": []}