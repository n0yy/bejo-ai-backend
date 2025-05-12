import logging
import os
from dotenv import load_dotenv

from langchain_google_community import GoogleDriveLoader
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_text_splitters import RecursiveCharacterTextSplitter


from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

# Simpan token agar bisa digunakan ulang
with open("token.json", "w") as token:
    token.write(creds.to_json())


from tqdm import tqdm

# === Load Environment Variables ===
load_dotenv()

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# === Constants ===
FOLDER_ID = "1WUx_0ztyjDt-e08SDoqqDePJnnxZXpIV"
TOKEN_PATH = "token.json"
QDRANT_URL = ":knowledge:"
COLLECTION_NAME = "knowledge_layer_1"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
BATCH_SIZE = 32

# === Step 1: Load Documents from Google Drive ===
logger.info("📥 Loading documents from Google Drive...")
loader = GoogleDriveLoader(
    folder_id=FOLDER_ID,
    token_path=TOKEN_PATH,
    recursive=False,
)
docs = loader.load()
logger.info(f"✅ Loaded {len(docs)} documents.")

# === Step 2: Split Documents into Chunks ===
logger.info("✂️ Splitting documents into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
)
all_splits = text_splitter.split_documents(docs)
logger.info(f"✅ Created {len(all_splits)} text chunks.")

# === Step 3: Create Embedding Model and Vector Store ===
logger.info("🔗 Initializing embedding model and vector store...")
embedding = OllamaEmbeddings(model="nomic-embed-text:latest")
qdrant = QdrantClient(host="localhost", port=6333)

qdrant.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)

vector_store = QdrantVectorStore(
    client=qdrant,
    collection_name=COLLECTION_NAME,
    embedding=embedding,
)
logger.info("✅ Qdrant vector store initialized.")

# === Step 4: Add Chunks to Vector Store in Batches with Progress Bar ===
logger.info("📦 Uploading chunks to Qdrant in batches...")
for i in tqdm(range(0, len(all_splits), BATCH_SIZE), desc="Uploading to Qdrant"):
    batch = all_splits[i : i + BATCH_SIZE]
    vector_store.add_documents(documents=batch)
logger.info("✅ All chunks uploaded to Qdrant successfully.")
