from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
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

# SQLite Database for Encodings & Events
conn = sqlite3.connect("radhe_events.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT,
        image_url TEXT,
        descriptor TEXT
    )
''')
conn.commit()

@app.get("/")
def home():
    return {"message": "Radhe Photography AI Server is Live!"}

# 1. Admin: Save Photo & Face Descriptors
@app.post("/admin/upload-face-data")
async def upload_face_data(
    event_id: str = Form(...),
    descriptor: str = Form(...),
    file: UploadFile = File(...)
):
    contents = await file.read()
    upload_result = cloudinary.uploader.upload(
        contents,
        folder=f"radhe_events/{event_id.lower()}"
    )
    img_url = upload_result.get("secure_url")

    cursor.execute(
        "INSERT INTO faces (event_id, image_url, descriptor) VALUES (?, ?, ?)",
        (event_id.lower(), img_url, descriptor)
    )
    conn.commit()
    return {"status": "success", "image_url": img_url}

# 2. Client: Get all face data for matching
@app.get("/client/event-faces/{event_id}")
def get_event_faces(event_id: str):
    cursor.execute("SELECT image_url, descriptor FROM faces WHERE event_id = ?", (event_id.lower(),))
    rows = cursor.fetchall()
    data = [{"image_url": r[0], "descriptor": r[1]} for r in rows]
    return {"status": "success", "faces": data}
