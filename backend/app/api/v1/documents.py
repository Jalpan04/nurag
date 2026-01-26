from fastapi import APIRouter, HTTPException
from app.db.db import get_db_connection
from app.core.chroma import get_chroma_client
from app.core.config import settings

router = APIRouter()

@router.get("/documents")
async def get_documents():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM documents ORDER BY created_at DESC")
        docs = [dict(row) for row in c.fetchall()]
        conn.close()
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/reset")
async def reset_brain():
    try:
        # 1. Truncate DB Table
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM documents") # Truncate equivalent
        conn.commit()
        conn.close()
        
        # 2. Reset Chroma Collection
        client = get_chroma_client()
        try:
            client.delete_collection(settings.CHROMA_COLLECTION_NAME)
        except Exception:
            pass # Collection might not exist
            
        # Recreate empty
        # client.create_collection(settings.CHROMA_COLLECTION_NAME)
        # Actually, ingest will imply creation, or we can leave it empty.
        
        return {"status": "success", "message": "Brain Core reset complete."}
    except Exception as e:
        print(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    try:
        # Delete from DB
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM documents WHERE filename = ?", (filename,))
        conn.commit()
        
        # Delete from Chroma
        client = get_chroma_client()
        collection = client.get_collection(settings.CHROMA_COLLECTION_NAME)
        
        # Delete where metadata['filename'] == filename
        # Chroma delete supports 'where' filter
        collection.delete(where={"filename": filename})
        # If older docs don't have this metadata, they won't be deleted. 
        # But for new system this works.
        
        conn.close()
        return {"status": "success", "deleted": filename}
    except Exception as e:
        print(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
