import os
import json
import logging

from dotenv import load_dotenv
from supabase import create_client, Client
from firebase_admin import credentials, initialize_app, firestore


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


load_dotenv()

# LOAD SUPABASE
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# LOAD FIREBASE ADMIN SDK
try:
    firebase_app = initialize_app(
        credential=credentials.Certificate(
            json.loads(os.environ.get("FIREBASE_CREDENTIALS"))
        )
    )
except ValueError:
    pass

db = firestore.client()
