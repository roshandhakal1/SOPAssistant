# SOP RAG Chatbot

A Streamlit-based chatbot that uses Google Gemini Flash Pro to answer questions about your Standard Operating Procedures (SOPs).

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
   - Copy `.env` file and update with your API key:
   ```bash
   GEMINI_API_KEY=your-actual-api-key-here
   ```

3. Run the app:
```bash
streamlit run app.py
```

## Features

- Processes PDF, DOCX, and DOC files
- Creates embeddings using Google Gemini
- Stores embeddings in ChromaDB vector database
- Web UI with chat interface
- Automatic update detection for new/modified files
- File hash-based caching to avoid reprocessing

## Usage

1. Click "Check for Updates" to process your SOP documents
2. Ask questions in the chat interface
3. View answers with referenced SOP titles
4. Re-click "Check for Updates" anytime to process new/changed files

## File Structure

- `app.py` - Main Streamlit application
- `document_processor.py` - Handles PDF/DOCX/DOC parsing
- `embeddings_manager.py` - Google Gemini embedding creation
- `vector_db.py` - ChromaDB vector database operations
- `rag_handler.py` - Query processing and response generation
- `config.py` - Configuration settings