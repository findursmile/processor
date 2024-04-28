import asyncio
import ssl
from traceback import print_exc
from keras import utils
from surrealdb import Surreal
from services import detect

# Disable SSL certificate verification
ssl._create_default_https_context = ssl._create_unverified_context


async def process_image_from_url(db, image):
    try:
        print(image["image_uri"])
        path = utils.get_file(origin=image["image_uri"])
        await db.query('UPDATE ' + image["id"] + ' SET status = "processing"')

        extract_face = detect.extract_face_from_image(path)

        if extract_face is None or not extract_face:
            await db.query('UPDATE ' + image["id"] + ' SET status = "no_faces_detected"')
            print("No faces detected in the image.")
            return None
        faces = detect.get_model_scores(extract_face)

        if faces is None or len(faces) == 0:
            await db.query('UPDATE ' + image["id"] + ' SET status = "no_faces_detected"')
            print("Unable to get model scores from the image.")
            return None

        for face in faces:
            face_encoding = await db.create(
                "face_encoding",
                {
                    "position": [],
                    "encoding": face.tolist(),
                }
            )
            await db.query(f"RELATE {image['id']}->face_of->{face_encoding[0]['id']}")
            print(f"Face encoding stored")
            await db.query('UPDATE ' + image["id"] + ' SET status = "processed"')
    except Exception as e:
        print("An error occurred while processing an image:")
        print_exc()


async def process_images_from_urls(db, results):
    try:
        for result in results:
            event_of = result.get("->event_of", {})
            out_data = event_of.get("out", [])
            [await process_image_from_url(db, image) for image in out_data]
    except Exception as e:
        print("An error occurred while processing images from URLs:")
        print_exc()


async def main(data):
    try:
        if isinstance(data, dict) and "event" in data:
            async with Surreal("ws://108.61.195.50:8000/rpc") as db:
                await db.signin({"user": "root", "pass": "root"})
                await db.use("test", "test")
                event = await db.query('select id,status,->event_of.out.* from event:' + data["event"])
                for item in event:
                    results = item.get("result", [])
                    if results:
                        await process_images_from_urls(db, results)
                    else:
                        print("No event data found.")
        else:
            print("Invalid data format or missing event key.")
    except Exception as e:
        print("An error occurred during main execution:")
        print_exc()


if __name__ == "__main__":
    asyncio.run(main(data=[]))
