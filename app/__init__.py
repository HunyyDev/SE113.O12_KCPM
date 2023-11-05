import os
from dotenv import load_dotenv
from mmdeploy_runtime import Detector
from supabase import create_client, Client
from firebase_admin import credentials, initialize_app
import json

import logging

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)


load_dotenv()

model_path = "./model"
detector = Detector(model_path=model_path, device_name="cpu", device_id=0)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


firebase_app = initialize_app(
    credential=credentials.Certificate(
        json.loads(os.environ.get("FIREBASE_CREDENTIALS"))
    )
)
