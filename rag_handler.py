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
        self.top_k = 50  # Maximum comprehensive SOP coverage for 1500+ documents
        self.abbreviation_mapper = AbbreviationMapper()
        self.model_name = model_name
    
    def query(self, question: str, top_k: int = None) -> Tuple[str, List[str]]:
        # Special handling for document count queries
        if any(phrase in question.lower() for phrase in ["how many sop", "count sop", "number of sop", "total sop"]):
            try:
                # Get actual count from vector database
                collection_info = self.vector_db.get_collection_info()
                unique_docs = collection_info.get('unique_documents', 0)
                total_chunks = collection_info.get('count', 0)
                
                # Get unique Google Drive documents
                gdrive_count = 0
                try:
                    results = self.vector_db.collection.get(include=['metadatas'])
                    if results and results.get('metadatas'):
                        gdrive_docs = set()
                        for metadata in results['metadatas']:
                            if 'gdrive_id' in metadata:
                                gdrive_docs.add(metadata['gdrive_id'])
                        gdrive_count = len(gdrive_docs)
                except:
                    pass
                
                response = f"""## 📊 SOP Database Statistics

**Total Unique SOPs**: {max(unique_docs, gdrive_count)} documents

**Details**:
• **Processed Documents**: {unique_docs} fully indexed SOPs
• **Google Drive References**: {gdrive_count} linked documents
• **Total Data Chunks**: {total_chunks} searchable segments

**Note**: The knowledge base contains both fully processed documents and Google Drive references for comprehensive coverage of your SOP library."""
                
                return response, []
            except Exception as e:
                pass
        if top_k is None:
            top_k = self.top_k
        
        # Get expanded query variations
        query_variations = self.abbreviation_mapper.expand_query(question)
        
        # Collect results from all query variations
        all_documents = []
        all_metadatas = []
        seen_ids = set()  # Track unique documents
        
        for query_variant in query_variations[:8]:  # Maximum query variations for comprehensive coverage
            query_embedding = self.embeddings_manager.create_query_embedding(query_variant)
            # Search with increased results per variation to get comprehensive coverage
            documents, metadatas = self.vector_db.search(query_embedding, top_k=min(top_k * 3, 100))
            
            # Add unique results
            for doc, meta in zip(documents, metadatas):
                doc_id = meta.get('id', doc[:50])  # Use ID or first 50 chars as identifier
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)
                    all_metadatas.append(meta)
        
        # If no results from expanded queries, try original query with higher results
        if not all_documents:
            query_embedding = self.embeddings_manager.create_query_embedding(question)
            all_documents, all_metadatas = self.vector_db.search(query_embedding, top_k=min(top_k * 3, 100))
        
        if not all_documents:
            return "I couldn't find any relevant information in the SOPs to answer your question. Try using full terms instead of abbreviations (e.g., 'accounts payable' instead of 'AP').", []
        
        # For maximum comprehensive search, use as many results as possible within token limits
        # Allow up to 4x the top_k to capture maximum relevant documents from all query variations
        # With 1500+ SOPs, aim for 100-200 document chunks for truly comprehensive answers
        max_results = min(len(all_documents), top_k * 4, 200)  # Cap at 200 for performance
        documents = all_documents[:max_results]
        metadatas = all_metadatas[:max_results]
        
        context = self._format_context(documents, metadatas)
        
        # Include query expansion info in prompt if abbreviation was expanded
        expansion_note = ""
        if len(query_variations) > 1:
            expansion_note = f"\nNote: Searched for variations including: {', '.join(query_variations[:3])}"
        
        prompt = f"""You are a comprehensive manufacturing assistant with access to an extensive knowledge base of Standard Operating Procedures (SOPs).{expansion_note}

COMPREHENSIVE SOP CONTEXT ({len(documents)} relevant documents from your knowledge base):
{context}

QUERY: {question}

FORMATTING AND RESPONSE INSTRUCTIONS:

**CRITICAL FORMATTING REQUIREMENTS:**
- Use clear headings with ## for main sections and ### for subsections
- Each bullet point (•) must be on its own separate line
- Add blank lines between bullet points for better readability
- Start each bullet point with a **bold category or key term**
- Group related information under logical section headings
- Use **bold text** for important terms, processes, and requirements
- Separate different aspects of the topic into distinct sections
- Never combine multiple bullet points into one paragraph

**COMPREHENSIVE ANALYSIS REQUIREMENTS:**
1. **MAXIMUM THOROUGHNESS**: Analyze ALL {len(documents)} provided documents comprehensively
2. **MULTI-SOP SYNTHESIS**: Cross-reference and synthesize information across ALL relevant SOPs
3. **COMPLETE COVERAGE**: Include all relevant procedures, requirements, and details
4. **DETAILED CITATIONS**: Cite specific SOP titles in quotes after each point
5. **STRUCTURED ORGANIZATION**: Organize into clear sections with descriptive headings

**REQUIRED RESPONSE FORMAT:**

## [Main Topic/Process Name]

### Key Requirements

• **[Category 1]**: [Detailed requirement description] ("[SOP Name]")

• **[Category 2]**: [Detailed requirement description] ("[SOP Name]", "[SOP Name]")

• **[Category 3]**: [Detailed requirement description] ("[SOP Name]")

### Step-by-Step Process

• **Step 1**: [Detailed description with specific actions] ("[SOP Name]")

• **Step 2**: [Detailed description with specific actions] ("[SOP Name]")

• **Step 3**: [Detailed description with specific actions] ("[SOP Name]")

### Safety and Compliance

• **[Safety Category]**: [Detailed safety requirement] ("[SOP Name]")

• **[Compliance Area]**: [Detailed compliance requirement] ("[SOP Name]")

• **[Additional Safety]**: [Additional safety measures] ("[SOP Name]")

### Quality Control

• **[QC Process]**: [Detailed quality control requirement] ("[SOP Name]")

• **[Verification]**: [Verification requirement details] ("[SOP Name]")

### Documentation Requirements

• **[Document Type]**: [Specific documentation requirement] ("[SOP Name]")

• **[Record Keeping]**: [Record keeping requirement] ("[SOP Name]")

**CRITICAL FORMATTING RULES:**
- Each bullet point must be on its own line with proper spacing
- Use double line breaks between bullet points for clarity
- Bold the key term at the start of each bullet point
- Keep bullet points focused and detailed but not too long
- Group related requirements under appropriate section headings

COMPREHENSIVE ANSWER:"""
        
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