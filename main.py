import os
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import Client, create_client

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Supabase Auth",
    description="FastAPI backend integrated with Supabase Client",
    version="1.0.0",
)

@app.get("/")
def read_root():
    return {
        "status": "active",
        "message": "FastAPI with Supabase client is successfully initialized.",
    }
