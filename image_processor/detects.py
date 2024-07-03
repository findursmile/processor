# image_processor/detects.py
import matplotlib.patches as patches
import mtcnn
from PIL import Image
from keras_vggface.utils import preprocess_input
from keras_vggface.vggface import VGGFace
from matplotlib import pyplot as plt
from numpy import asarray

detector = mtcnn.MTCNN()
model = VGGFace(
        model='resnet50',
        include_top=False,
        input_shape=(224, 224, 3),
        pooling='avg'
        )

async def extract_face_from_image(image_path, required_size=(224, 224)):
    try:
        image = plt.imread(image_path)
        faces = detector.detect_faces(image)

        if faces is None:
            print("No faces detected in the image.")
            return None

        face_images = []

        for face in faces:
            x1, y1, width, height = face['box']
            x2, y2 = x1 + width, y1 + height

            face_boundary = image[y1:y2, x1:x2]

            face_image = Image.fromarray(face_boundary)
            face_image = face_image.resize(required_size)
            face_array = asarray(face_image)
            face_images.append(face_array)

        return face_images
    except Exception as e:
        print(f"An error occurred while extracting faces from image: {e}")
        return []


async def get_model_scores(faces):
    try:
        samples = asarray(faces, 'float32')
        samples = preprocess_input(samples, version=2)

        scores = model.predict(samples)

        return scores

    except Exception as e:
        print(f"An error occurred while getting model scores: {e}")
        return None
