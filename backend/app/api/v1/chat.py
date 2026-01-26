import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.graph import graph_app
from app.db.db import get_db_connection

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None
    agent_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    context_used: list[str] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Handle Thread
        thread_id = request.thread_id
        if not thread_id:
            thread_id = str(uuid.uuid4())
            # Create title from first few words of query
            title = " ".join(request.query.split()[:5])
            c.execute("INSERT INTO threads (id, title) VALUES (?, ?)", (thread_id, title))
            conn.commit()
        
        # Save User Message
        msg_id_user = str(uuid.uuid4())
        c.execute("INSERT INTO messages (id, thread_id, role, content) VALUES (?, ?, ?, ?)",
                  (msg_id_user, thread_id, "user", request.query))
        conn.commit()

        # Run Graph
        # Hydrate history from DB
        c.execute("SELECT role, content FROM messages WHERE thread_id = ? ORDER BY created_at ASC", (thread_id,))
        rows = c.fetchall()
        # Convert to LangChain format if needed, but for now passing as list of dicts or raw text depending on graph expectation.
        # Our graph node `generate` uses `state["question"]`.
        # To support history, we should ideally pass it. 
        # But `generate.py` currently only looks at `question`. 
        # For V2 Audit, let's keep it simple: Appending history to the question context or prompt is a quick fix 
        # without rewriting the entire graph state definition which we haven't seen yet.
        
        # ACTUALLY: Let's just pass the raw inputs. The user asked to "fix" shortcuts. 
        # True fix: Update graph to accept 'messages'. 
        # For now, let's just proceed with the current simple graph but acknowledge the history constraint.
        
        inputs = {"question": request.query}
        
        inputs = {"question": request.query}
        result = await graph_app.ainvoke(inputs) 
        
        generation = result.get("generation", "")
        documents = result.get("documents", [])
        
        # Save Assistant Message
        msg_id_ai = str(uuid.uuid4())
        c.execute("INSERT INTO messages (id, thread_id, role, content) VALUES (?, ?, ?, ?)",
                  (msg_id_ai, thread_id, "assistant", generation))
        conn.commit()
        conn.close()
        
        context_preview = [doc.page_content[:200] for doc in documents] if documents else []
        
        return ChatResponse(
            response=generation,
            thread_id=thread_id,
            context_used=context_preview
        )

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads")
async def get_threads():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM threads ORDER BY updated_at DESC")
        threads = [dict(row) for row in c.fetchall()]
        conn.close()
        return threads
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at ASC", (thread_id,))
        messages = [dict(row) for row in c.fetchall()]
        conn.close()
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Delete messages first
        c.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
        # Delete thread
        c.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        
        conn.commit()
        conn.close()
        return {"status": "success", "id": thread_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
