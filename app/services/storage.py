from supabase import create_client
from app.core.config import get_settings
import uuid

settings = get_settings()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class StorageService:
    @staticmethod
    def upload_file(file_content: bytes, filename: str, bucket: str = "documents") -> str:
        file_path = f"{uuid.uuid4()}_{filename}"
        
        supabase.storage.from_(bucket).upload(
            file_path,
            file_content,
            file_options={"content-type": "application/pdf"}
        )
        
        url = supabase.storage.from_(bucket).get_public_url(file_path)
        return url
    
    @staticmethod
    def delete_file(file_url: str, bucket: str = "documents"):
        file_path = file_url.split("/")[-1]
        supabase.storage.from_(bucket).remove([file_path])