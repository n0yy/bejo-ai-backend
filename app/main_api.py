import uvicorn
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import dari direktori lokal
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.api import app

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Log startup info
    logger.info("Starting BEJO AI API server...")
    logger.info(f"API loaded with FastAPI version: {uvicorn.__version__}")
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    ) 