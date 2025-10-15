import re
from typing import List, Dict
import pdfplumber
from docx import Document as DocxDocument

class RFPParser:
    @staticmethod
    def extract_questions(file_path: str, file_type: str) -> List[str]:
        if file_type.endswith('.pdf'):
            text = RFPParser._extract_pdf_text(file_path)
        elif file_type.endswith('.docx'):
            text = RFPParser._extract_docx_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return RFPParser._parse_questions(text)
    
    @staticmethod
    def _extract_pdf_text(file_path: str) -> str:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    
    @staticmethod
    def _extract_docx_text(file_path: str) -> str:
        doc = DocxDocument(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    
    @staticmethod
    def _parse_questions(text: str) -> List[str]:
        questions = []
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            if line.endswith('?'):
                questions.append(line)
            elif re.match(r'^\d+[\.\)]\s+', line):
                questions.append(re.sub(r'^\d+[\.\)]\s+', '', line))
            elif any(line.lower().startswith(prefix) for prefix in ['describe', 'explain', 'what', 'how', 'do you', 'does your', 'can you', 'provide']):
                questions.append(line)
        
        return questions