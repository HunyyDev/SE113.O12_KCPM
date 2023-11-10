import os
from supabase import create_client, Client
from .. import logger

logger.info("Connecting to supabase")
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabaseClient: Client = create_client(url, key)
