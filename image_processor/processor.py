import asyncio
import os
from keras import utils
from surrealdb import Surreal
from image_processor.detects import extract_face_from_image, get_model_scores

async def handle_event(data):
    pr = Processor()
    await pr.init_db()
    await pr.handle_event(data)

class Processor:
    async def init_db(self):
        url = "{}://{}:{}/rpc".format(
                os.environ['SURREALDB_SCHEMA'],
                os.environ['SURREALDB_HOST'],
                os.environ['SURREALDB_PORT'])
        self.db = Surreal(url)
        await self.db.connect()
        await self.db.signin({"user": os.environ['SURREALDB_USERNAME'], "pass": os.environ['SURREALDB_PASSWORD']})
        await self.db.use(os.environ['SURREALDB_NAMESPACE'], os.environ['SURREALDB_DATABASE'])

    async def close_db(self):
        await self.db.close()

    async def get_face_encodings(self, image):
        print(f"processing {image['id']}")
        path = utils.get_file(origin=f'{os.environ["ASSETS_URL"]}/{image["image_uri"]}')
        extract_face = await extract_face_from_image(path)

        if not extract_face:
            print("No faces detected in the image.")
            return [], image['id']

        faces = await get_model_scores(extract_face)

        if faces is None or len(faces) == 0:
            print("Unable to get model scores from the image.")
            return [], image['id']

        return faces, image['id']

    async def store_encodings(self, encodings, imageId):
        if len(encodings) == 0:
            await self.db.query(f'UPDATE {imageId} SET status = "no_faces_detected"')
            print("No faces were found")

        for encoding in encodings:
            face_encoding = await self.db.create(
                "face_encoding",
                {"position": [], "encoding": encoding.tolist(), "image": imageId}
            )
            await self.db.query(f"RELATE {imageId}->face_of->{face_encoding[0]['id']}")

        await self.db.query(f'UPDATE {imageId} SET status = "processed"')

        print("Face encoding stored")

    async def handle_event(self, data):
        try:
            if isinstance(data, dict) and "event" in data:
                event = await self.db.query(f'select * from image where event = {data["event"]} and status="pending"')
                for item in event:
                    results = item.get("result", [])
                    if results:
                        detection_encodings = await asyncio.gather(*[self.get_face_encodings(image) for image in results])
                        for detection in detection_encodings:
                            await self.store_encodings(detection[0], detection[1]);
                    else:
                        print("No event data found.")
            else:
                print("Invalid data format or missing event key.")
        except Exception as e:
            print("An error occurred during handle_event:" )
            print(e)

    async def find_images(self, event_id, faces):
        where = []
        for face in faces:
            where.append(f'vector::similarity::cosine({face.tolist()}, out.encoding) > 0.6')

        sql = f'select * from image where event={event_id} and ->(face_of where '
        sql = sql + ' OR '.join(where) + ')'

        results = await self.db.query(sql)

        if len(results) and results[0]['status'] == 'OK':
            print(results[0])
            return results[0]['result']

        return []
