from fastapi import FastAPI, UploadFile
from image_processor.detects import extract_face_from_image, get_model_scores
from dotenv import load_dotenv
import tempfile

from image_processor.processor import Processor

load_dotenv()
app = FastAPI()

@app.post("/events/{event_id}/images")
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

    p = Processor()
    await p.init_db()
    await p.find_images(faces)

    return []
