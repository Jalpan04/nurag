

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import chat, ingest, graph, agents, documents

from app.db.db import init_db

app = FastAPI(title="Nurag API")

# Initialize DB
init_db()

# CORS (Allow Next.js frontend)
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix=settings.API_V1_STR, tags=["chat"])
app.include_router(ingest.router, prefix=settings.API_V1_STR, tags=["ingest"])
app.include_router(graph.router, prefix=settings.API_V1_STR, tags=["graph"])
app.include_router(agents.router, prefix=settings.API_V1_STR, tags=["agents"])
app.include_router(documents.router, prefix=settings.API_V1_STR, tags=["documents"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
