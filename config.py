import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        # Cloud Run compatible paths - use /tmp for writable storage
        self.SOP_FOLDER = os.getenv("SOP_FOLDER", "/tmp/documents")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "/tmp/chroma_db")
        
        # Ensure directories exist
        os.makedirs(self.SOP_FOLDER, exist_ok=True)
        os.makedirs(self.CHROMA_PERSIST_DIR, exist_ok=True)
        
        self.CHUNK_SIZE = 1000
        self.CHUNK_OVERLAP = 200
        
        self.EMBEDDING_BATCH_SIZE = 100
        
        self.TOP_K_RESULTS = 50  # Maximum comprehensive coverage for 1500+ SOPs
        
        # Model Configuration (can be overridden by user settings)
        self.DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")
        self.EXPERT_MODEL = os.getenv("EXPERT_MODEL", "gemini-1.5-pro")
        self.EXPERT_CONFIDENCE_THRESHOLD = float(os.getenv("EXPERT_CONFIDENCE_THRESHOLD", "0.7"))
        self.EXPERT_MAX_CONTEXT_LENGTH = int(os.getenv("EXPERT_MAX_CONTEXT_LENGTH", "5"))
        self.EXPERT_TEMPERATURE = float(os.getenv("EXPERT_TEMPERATURE", "0.7"))
        
        # Expert consultation types
        self.CONSULTATION_TYPES = [
            "innovation",
            "production", 
            "quality",
            "supply_chain",
            "financial",
            "strategic",
            "general"
        ]
        
        # Google Drive configuration
        self.GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1etIfvZ8BNzCTkJ-X70fLoMa4E-KTb-zh")
        self.AUTO_SYNC_ON_STARTUP = os.getenv("AUTO_SYNC_ON_STARTUP", "true").lower() == "true"
        
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it as an environment variable:\n"
                "export GEMINI_API_KEY='your-api-key-here'"
            )
        
        # Create documents folder if it doesn't exist
        Path(self.SOP_FOLDER).mkdir(exist_ok=True)