from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.chroma import get_chroma_client
from app.core.config import settings
from app.db.db import get_db_connection
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader, BSHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import shutil
import uuid

router = APIRouter()

@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    try:
        # Save temp file
        file_id = str(uuid.uuid4())
        file_path = f"/tmp/{file_id}_{file.filename}"
        os.makedirs("/tmp", exist_ok=True)
        
        # Save upload to temp
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        try:
            # Load and split
            ext = os.path.splitext(file.filename)[1].lower()
            
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif ext in [".html", ".htm"]:
                loader = BSHTMLLoader(file_path)
            elif ext in [".txt", ".md", ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".json", ".yaml", ".yml", ".sh", ".bat", ".ps1", ".css", ".sql", ".xml"]:
                 loader = TextLoader(file_path, autodetect_encoding=True)
            else:
                 raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Supported: PDF, HTML, Code, Text, MD.")
    
            docs = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=1000, chunk_overlap=200
            )
            doc_splits = text_splitter.split_documents(docs)
            
            # Add filename metadata for deletion
            for doc in doc_splits:
                doc.metadata["filename"] = file.filename
            
            # Embed and Store
            emb_model = OllamaEmbeddings(base_url=settings.OLLAMA_BASE_URL, model=settings.EMBEDDING_MODEL)
            
            # We iterate to persist to the same chroma db path
            client = get_chroma_client()
            vectorstore = Chroma(
                client=client,
                collection_name=settings.CHROMA_COLLECTION_NAME,
                embedding_function=emb_model,
            )
            
            vectorstore.add_documents(documents=doc_splits)
            
            # Save to DB
            conn = get_db_connection()
            c = conn.cursor()
            doc_id = str(uuid.uuid4())
            c.execute("INSERT INTO documents (id, filename) VALUES (?, ?)", (doc_id, file.filename))
            conn.commit()
            conn.close()
            
            return {"status": "success", "filename": file.filename, "chunks": len(doc_splits)}

        finally:
            # Cleanup guaranteed
            if os.path.exists(file_path):
                os.remove(file_path)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
