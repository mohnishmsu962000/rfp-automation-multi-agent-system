from langchain_text_splitters import RecursiveCharacterTextSplitter
import pdfplumber
from docx import Document as DocxDocument
import openpyxl
from typing import List, Dict

class DocumentProcessor:
    @staticmethod
    def extract_text(file_path: str, file_type: str) -> str:
        if file_type.endswith('.pdf'):
            return DocumentProcessor._extract_pdf(file_path)
        elif file_type.endswith('.docx'):
            return DocumentProcessor._extract_docx(file_path)
        elif file_type.endswith(('.xlsx', '.xls')):
            return DocumentProcessor._extract_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    @staticmethod
    def _extract_pdf(file_path: str) -> str:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    
    @staticmethod
    def _extract_docx(file_path: str) -> str:
        doc = DocxDocument(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    
    @staticmethod
    def _extract_excel(file_path: str) -> str:
        wb = openpyxl.load_workbook(file_path)
        text = ""
        for sheet in wb:
            for row in sheet.iter_rows(values_only=True):
                text += " ".join([str(cell) for cell in row if cell]) + "\n"
        return text
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[Dict[str, any]]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        
        chunks = text_splitter.split_text(text)
        
        return [
            {
                "text": chunk,
                "index": i,
                "metadata": {"char_count": len(chunk)}
            }
            for i, chunk in enumerate(chunks)
        ]