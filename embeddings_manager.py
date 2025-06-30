import google.generativeai as genai
from typing import List
import time
import numpy as np

class EmbeddingsManager:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = 'models/text-embedding-004'
        self.batch_size = 100
        self.max_retries = 3
        self.retry_delay = 1
    
    def create_embeddings(self, texts: List[str], progress_callback=None) -> List[List[float]]:
        embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        for batch_num, i in enumerate(range(0, len(texts), self.batch_size)):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._embed_batch(batch)
            embeddings.extend(batch_embeddings)
            
            if progress_callback:
                progress_callback((batch_num + 1) / total_batches)
        
        return embeddings
    
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        for attempt in range(self.max_retries):
            try:
                result = genai.embed_content(
                    model=self.model,
                    content=texts,
                    task_type="retrieval_document",
                    title="SOP Document"
                )
                
                return [embedding for embedding in result['embedding']]
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"Failed to create embeddings after {self.max_retries} attempts: {str(e)}")
        
        return []
    
    def create_query_embedding(self, query: str) -> List[float]:
        for attempt in range(self.max_retries):
            try:
                result = genai.embed_content(
                    model=self.model,
                    content=query,
                    task_type="retrieval_query"
                )
                
                return result['embedding']
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"Failed to create query embedding after {self.max_retries} attempts: {str(e)}")