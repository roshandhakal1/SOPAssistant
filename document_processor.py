import os
from pathlib import Path
from typing import List, Dict
import PyPDF2
from docx import Document
import tempfile
import platform

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_file(self, file_path: str) -> List[Dict]:
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            text = self._extract_pdf_text(file_path)
        elif extension == '.docx':
            text = self._extract_docx_text(file_path)
        elif extension == '.doc':
            text = self._extract_doc_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        chunks = self._split_text(text)
        
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                'content': chunk,
                'metadata': {
                    'source': str(file_path),
                    'filename': file_path.name,
                    'chunk_id': i,
                    'file_type': extension[1:]
                }
            })
        
        return documents
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    
    def _extract_docx_text(self, file_path: Path) -> str:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + "\t"
                text += "\n"
        
        return text
    
    def _extract_doc_text(self, file_path: Path) -> str:
        if platform.system() == "Windows":
            try:
                import win32com.client
                import pythoncom
                pythoncom.CoInitialize()
                try:
                    word = win32com.client.Dispatch("Word.Application")
                    word.Visible = False
                    doc = word.Documents.Open(str(file_path))
                    text = doc.Range().Text
                    doc.Close()
                    word.Quit()
                    return text
                finally:
                    pythoncom.CoUninitialize()
            except ImportError:
                pass
        
        if platform.system() == "Darwin":
            try:
                import subprocess
                result = subprocess.run(
                    ['textutil', '-stdout', '-convert', 'txt', str(file_path)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        try:
            from doc2docx import convert
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
                tmp_path = tmp.name
            
            convert(str(file_path), tmp_path)
            text = self._extract_docx_text(Path(tmp_path))
            os.unlink(tmp_path)
            return text
        except Exception as e:
            raise Exception(f"Unable to read .doc file. Please install python-docx-win32 on Windows or ensure textutil is available on macOS: {str(e)}")
    
    def _split_text(self, text: str) -> List[str]:
        chunks = []
        sentences = text.replace('\n', ' ').split('. ')
        
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        overlapped_chunks = []
        for i in range(len(chunks)):
            if i == 0:
                overlapped_chunks.append(chunks[i])
            else:
                overlap_text = chunks[i-1][-self.chunk_overlap:] if len(chunks[i-1]) > self.chunk_overlap else chunks[i-1]
                overlapped_chunks.append(overlap_text + " " + chunks[i])
        
        return overlapped_chunks