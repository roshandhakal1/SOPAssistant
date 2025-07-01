import google.generativeai as genai
from typing import List, Tuple, Dict
from embeddings_manager import EmbeddingsManager
from abbreviation_mapper import AbbreviationMapper
import numpy as np

class RAGHandler:
    def __init__(self, api_key: str, vector_db, model_name: str = 'gemini-1.5-flash'):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.vector_db = vector_db
        self.embeddings_manager = EmbeddingsManager(api_key)
        self.top_k = 5
        self.abbreviation_mapper = AbbreviationMapper()
        self.model_name = model_name
    
    def query(self, question: str, top_k: int = None) -> Tuple[str, List[str]]:
        if top_k is None:
            top_k = self.top_k
        
        # Get expanded query variations
        query_variations = self.abbreviation_mapper.expand_query(question)
        
        # Collect results from all query variations
        all_documents = []
        all_metadatas = []
        seen_ids = set()  # Track unique documents
        
        for query_variant in query_variations[:3]:  # Limit to top 3 variations to avoid too many searches
            query_embedding = self.embeddings_manager.create_query_embedding(query_variant)
            documents, metadatas = self.vector_db.search(query_embedding, top_k=top_k)
            
            # Add unique results
            for doc, meta in zip(documents, metadatas):
                doc_id = meta.get('id', doc[:50])  # Use ID or first 50 chars as identifier
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
                    all_metadatas.append(meta)
        
        # If no results from expanded queries, try original query
        if not all_documents:
            query_embedding = self.embeddings_manager.create_query_embedding(question)
            all_documents, all_metadatas = self.vector_db.search(query_embedding, top_k=top_k)
        
        if not all_documents:
            return "I couldn't find any relevant information in the SOPs to answer your question. Try using full terms instead of abbreviations (e.g., 'accounts payable' instead of 'AP').", []
        
        # Limit to top k results
        documents = all_documents[:top_k]
        metadatas = all_metadatas[:top_k]
        
        context = self._format_context(documents, metadatas)
        
        # Include query expansion info in prompt if abbreviation was expanded
        expansion_note = ""
        if len(query_variations) > 1:
            expansion_note = f"\nNote: Searched for variations including: {', '.join(query_variations[:3])}"
        
        prompt = f"""You are a helpful assistant that answers questions based on Standard Operating Procedures (SOPs).{expansion_note}

Context from SOPs:
{context}

Question: {question}

Instructions:
1. Answer the question comprehensively based on the provided SOP context
2. Be specific and cite the relevant SOP titles when referencing information (use plain text, no HTML)
3. If the context doesn't contain enough information to fully answer the question, say so
4. Structure your answer clearly with bullet points or numbered lists when appropriate
5. For questions about processes or lifecycles, list ALL steps in order with detailed explanations
6. Provide thorough, detailed responses - do not summarize or abbreviate unless asked
7. Include all relevant details, procedures, requirements, and considerations from the SOPs
8. Use plain text formatting only - no HTML tags or special formatting

Answer:"""
        
        # Configure generation with maximum output tokens
        generation_config = {
            "max_output_tokens": 8192,  # Maximum allowed for Gemini
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 40
        }
        
        response = self.model.generate_content(prompt, generation_config=generation_config)
        answer = response.text
        
        # Format SOP names in the response with HTML spans
        import re
        # More precise pattern to match SOP filenames (including revision numbers and special characters)
        sop_pattern = r'\b([A-Za-z0-9\-\_\(\)\s]+(?:Rev\d+(?:Draft\d+)?)?[A-Za-z0-9\-\_\(\)\s]*\.(doc|docx|pdf))\b'
        
        def format_sop(match):
            sop_name = match.group(1)
            # Clean up any existing HTML tags
            clean_name = re.sub(r'<[^>]+>', '', sop_name)
            return f'<span class="sop-reference-inline">{clean_name}</span>'
        
        # Replace SOP names with formatted versions, but avoid double-formatting
        if '<span class="sop-reference-inline">' not in answer:
            formatted_answer = re.sub(sop_pattern, format_sop, answer)
        else:
            formatted_answer = answer
        
        # Return sources with metadata (including Google Drive links if available)
        sources_with_metadata = []
        seen_files = set()
        for meta in metadatas:
            filename = meta['filename']
            if filename not in seen_files:
                seen_files.add(filename)
                source_info = {'filename': filename}
                if 'gdrive_link' in meta:
                    source_info['gdrive_link'] = meta['gdrive_link']
                sources_with_metadata.append(source_info)
        
        return formatted_answer, sources_with_metadata
    
    def _format_context(self, documents: List[str], metadatas: List[Dict]) -> str:
        context_parts = []
        
        for doc, meta in zip(documents, metadatas):
            context_parts.append(f"**From {meta['filename']}:**\n{doc}\n")
        
        return "\n---\n".join(context_parts)