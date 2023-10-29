import os
from dotenv import load_dotenv
from mmdeploy_runtime import Detector
from supabase import create_client, Client

load_dotenv()

model_path = "./model"
detector = Detector(model_path=model_path, device_name="cpu", device_id=0)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
