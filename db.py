from astrapy import DataAPIClient
from dotenv import load_dotenv
import streamlit as st
import os

# Load .env variables
load_dotenv()

# Pull Astra DB credentials from environment
ENDPOINT = os.getenv("ASTRA_ENDPOINT")
TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")

# Cache the DB connection using Streamlit
@st.cache_resource
def get_db():
    client = DataAPIClient(TOKEN)
    db = client.get_database_by_api_endpoint(ENDPOINT)
    return db

# Connect to the database
db = get_db()

# Access existing collections (do NOT try to create them)
personal_data_collection = db.get_collection("personal_data")
notes_collection = db.get_collection("notes")
