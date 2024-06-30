import asyncio
import os
import traceback
from keras import utils
from surrealdb import Surreal
from image_processor.detects import extract_face_from_image, get_model_scores


async def process_image_from_url(db, image):
    try:
        path = utils.get_file(origin=f'{os.environ["ASSETS_URL"]}/{image["image_uri"]}')
        await db.query(f'UPDATE {image["id"]} SET status = "processing"')

        extract_face = extract_face_from_image(path)

        if not extract_face:
            await db.query(f'UPDATE {image["id"]} SET status = "no_faces_detected"')
            print("No faces detected in the image.")
            return

        faces = get_model_scores(extract_face)

        if not faces or len(faces):
            await db.query(f'UPDATE {image["id"]} SET status = "no_faces_detected"')
            print("Unable to get model scores from the image.")
            return

        for face in faces:
            face_encoding = await db.create(
                "face_encoding",
                {"position": [], "encoding": face.tolist()}
            )
            await db.query(f"RELATE {image['id']}->face_of->{face_encoding[0]['id']}")
            print("Face encoding stored")

        await db.query(f'UPDATE {image["id"]} SET status = "processed"')
    except Exception as e:
        print("An error occurred while processing an image:")
        traceback.print_exception(e)


async def handle_event(data, db=None):
    try:
        url = "{}://{}:{}/rpc".format(
                os.environ['SURREALDB_SCHEMA'],
                os.environ['SURREALDB_HOST'],
                os.environ['SURREALDB_PORT'])
        async with Surreal(url) as db:
            await db.signin({"user": os.environ['SURREALDB_USERNAME'], "pass": os.environ['SURREALDB_PASSWORD']})
            await db.use(os.environ['SURREALDB_NAMESPACE'], os.environ['SURREALDB_DATABASE'])
            if isinstance(data, dict) and "event" in data:
                event = await db.query(f'select * from image where event = {data["event"]}')
                for item in event:
                    results = item.get("result", [])
                    if results:
                        for image in results:
                             await process_image_from_url(db, image)
                    else:
                        print("No event data found.")
            else:
                print("Invalid data format or missing event key.")
    except Exception as e:
        print("An error occurred during main execution:" )
        print(e)
        traceback.print_exception(e)

