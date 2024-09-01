from fastapi import FastAPI, UploadFile
from image_processor.detects import extract_face_from_image, get_model_scores
from dotenv import load_dotenv
import tempfile
from fastapi.middleware.cors import CORSMiddleware
from image_processor.processor import Processor

load_dotenv()
app = FastAPI()

origins=[
        "http://localhost:5173",
        "http://localhost:5174"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_processor():
    p = Processor()
    await p.init_db()
    return p

@app.get("/events/{event_id}")
async def event_detail(event_id: str):
    p = await get_processor()
    results = await p.db.query(f'select * from event where id = {event_id}')

    if len(results) and results[0]['status'] == 'OK':
        return results[0]['result']

@app.post("/events/{event_id}/images")
async def find_images(event_id: str, file: UploadFile):
    tmpFile = tempfile.NamedTemporaryFile()

    tmpFile.write(await file.read())
    extract_face = await extract_face_from_image(tmpFile.name)

    if not extract_face:
        print("No faces detected in the image.")
        return []

    faces = await get_model_scores(extract_face)

    if faces is None or len(faces) == 0:
        print("Unable to get model scores from the image.")
        return []

    p = await get_processor()
    return await p.find_images(event_id, faces)

@app.post("/image/face_encodings")
async def face_encodings(file: UploadFile):
    tmpFile = tempfile.NamedTemporaryFile()

    tmpFile.write(await file.read())
    extract_face = await extract_face_from_image(tmpFile.name)

    if not extract_face:
        print("No faces detected in the image.")
        return []

    faces = await get_model_scores(extract_face)

    if faces is None or len(faces) == 0:
        print("Unable to get model scores from the image.")
        return []

    return list(map(lambda f: f.tolist(), faces))
