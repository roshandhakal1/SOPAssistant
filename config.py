import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.SOP_FOLDER = os.getenv("SOP_FOLDER", "/Users/roshandhakal/Desktop/AD/SOPs")
        
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        
        self.CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        self.CHUNK_SIZE = 1000
        self.CHUNK_OVERLAP = 200
        
        self.EMBEDDING_BATCH_SIZE = 100
        
        self.TOP_K_RESULTS = 5
        
        # Expert Mode Configuration
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
        
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it as an environment variable:\n"
                "export GEMINI_API_KEY='your-api-key-here'"
            )
        
        if not Path(self.SOP_FOLDER).exists():
            raise ValueError(f"SOP folder not found: {self.SOP_FOLDER}")