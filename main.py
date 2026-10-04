from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import face_recognition
import numpy as np
import io
import json
import sqlite3
import cloudinary
import cloudinary.uploader

# Cloudinary Configuration
cloudinary.config(
    cloud_name="ofjrct6b",
    api_key="962823728611994",
    api_secret="z5wDhzrZVCUHrAZL7dutMb5UM0w",
    secure=True
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite Database for Encodings
conn = sqlite3.connect("radhe_events.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT,
        image_url TEXT,
        encoding TEXT
    )
''')
conn.commit()

@app.get("/")
def home():
    return {"message": "Radhe Photography AI Server is Live!"}

# 1. Admin: Upload Photo & Save Face Data
@app.post("/admin/upload-photo")
async def upload_event_photo(
    event_id: str = Form(...),
    file: UploadFile = File(...)
):
    contents = await file.read()
    
    # Cloudinary par upload karna
    upload_result = cloudinary.uploader.upload(
        contents,
        folder=f"radhe_events/{event_id.lower()}"
    )
    img_url = upload_result.get("secure_url")

    # AI se faces detect karna
    image = face_recognition.load_image_file(io.BytesIO(contents))
    encodings = face_recognition.face_encodings(image)

    for enc in encodings:
        enc_str = json.dumps(enc.tolist())
        cursor.execute(
            "INSERT INTO faces (event_id, image_url, encoding) VALUES (?, ?, ?)",
            (event_id.lower(), img_url, enc_str)
        )
    conn.commit()

    return {"status": "success", "image_url": img_url, "faces_found": len(encodings)}

# 2. Client: Selfie search
@app.post("/client/search-face")
async def search_client_face(
    event_id: str = Form(...),
    selfie: UploadFile = File(...)
):
    contents = await selfie.read()
    selfie_img = face_recognition.load_image_file(io.BytesIO(contents))
    selfie_encodings = face_recognition.face_encodings(selfie_img)

    if len(selfie_encodings) == 0:
        return {"status": "no_face_in_selfie", "photos": []}

    target_encoding = selfie_encodings[0]

    cursor.execute("SELECT image_url, encoding FROM faces WHERE event_id = ?", (event_id.lower(),))
    rows = cursor.fetchall()

    matched_urls = set()
    for img_url, enc_str in rows:
        db_encoding = np.array(json.loads(enc_str))
        matches = face_recognition.compare_faces([db_encoding], target_encoding, tolerance=0.45)
        if matches[0]:
            matched_urls.add(img_url)

    return {"status": "success", "photos": list(matched_urls)}
