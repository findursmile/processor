# image_processor/processor.py
import asyncio
from traceback import print_exc
from keras import utils
from detects import extract_face_from_image, get_model_scores


async def process_image_from_url(db, image):
    try:
        print(image["image_uri"])
        path = utils.get_file(origin=image["image_uri"])
        await db.query(f'UPDATE {image["id"]} SET status = "processing"')

        extract_face = extract_face_from_image(path)

        if not extract_face:
            await db.query(f'UPDATE {image["id"]} SET status = "no_faces_detected"')
            print("No faces detected in the image.")
            return

        faces = get_model_scores(extract_face)

        if not faces:
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


async def handle_event(data, db):
    try:
        if isinstance(data, dict) and "event" in data:
            event = await db.query(f'select id,status,->event_of.out.* from event:{data["event"]}')
            for item in event:
                results = item.get("result", [])
                if results:
                    for result in results:
                        out_data = result.get("->event_of", {}).get("out", [])
                        await asyncio.gather(*[process_image_from_url(db, image) for image in out_data])
                else:
                    print("No event data found.")
        else:
            print("Invalid data format or missing event key.")
    except Exception as e:
        print("An error occurred during main execution:")

