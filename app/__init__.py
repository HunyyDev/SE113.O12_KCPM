import os
import json
import logging

from dotenv import load_dotenv
from mmdeploy_runtime import Detector
from supabase import create_client, Client
from firebase_admin import credentials, initialize_app, firestore
from neo4j import GraphDatabase


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


load_dotenv()

# LOAD MODEL
model_path = "./model"
detector = Detector(model_path=model_path, device_name="cpu", device_id=0)

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

# LOAD NEO4J DB
URI = os.environ.get("NEO4J_URI")
AUTH = (os.environ.get("NEO4J_USERNAME"), os.environ.get("NEO4J_PASSWORD"))
driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()
driver.execute_query(
    "CREATE CONSTRAINT uid IF NOT EXISTS FOR (p:Person) REQUIRE p.uid IS UNIQUE"
)
