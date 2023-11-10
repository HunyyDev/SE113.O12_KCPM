import os
import json
import logging

from dotenv import load_dotenv
from mmdeploy_runtime import Detector
from firebase_admin import credentials, initialize_app, firestore


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

logger.info("Loading model")
model_path = "./model"
detector = Detector(model_path=model_path, device_name="cpu", device_id=0)


# LOAD FIREBASE ADMIN SDK
logger.info("Connecting to firebase")
firebase_app = initialize_app(
    credential=credentials.Certificate(
        json.loads(os.environ.get("FIREBASE_CREDENTIALS"))
    )
)
db = firestore.client()
