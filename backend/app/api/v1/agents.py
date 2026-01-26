import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.db import get_db_connection
import httpx
from app.core.config import settings

router = APIRouter()

class AgentCreate(BaseModel):
    name: str
    system_prompt: str
    model: str = "gemma3:latest"

class AgentResponse(BaseModel):
    id: str
    name: str
    system_prompt: str
    model: str
    is_active: bool

class AgentUpdate(BaseModel):
    name: str
    system_prompt: str
    model: str

@router.get("/agents", response_model=list[AgentResponse])
async def get_agents():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM agents")
        rows = c.fetchall()
        
        agents = []
        for row in rows:
            agents.append(AgentResponse(
                id=row["id"],
                name=row["name"],
                system_prompt=row["system_prompt"],
                model=row["model"],
                is_active=bool(row["is_active"])
            ))
        conn.close()
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        agent_id = str(uuid.uuid4())
        c.execute("INSERT INTO agents (id, name, system_prompt, model, is_active) VALUES (?, ?, ?, ?, 0)",
                  (agent_id, agent.name, agent.system_prompt, agent.model))
        conn.commit()
        
        return AgentResponse(
            id=agent_id,
            name=agent.name,
            system_prompt=agent.system_prompt,
            model=agent.model,
            is_active=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/models")
async def get_ollama_models():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code != 200:
                return ["gemma3:latest"]
            
            data = resp.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
    except Exception as e:
        print(f"Ollama fetch error: {e}")
        return ["gemma3:latest"]

@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, agent: AgentUpdate):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("UPDATE agents SET name = ?, system_prompt = ?, model = ? WHERE id = ?",
                  (agent.name, agent.system_prompt, agent.model, agent_id))
        
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        conn.commit()
        conn.close()
        return {"status": "success", "id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}/select")
async def select_agent(agent_id: str):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("UPDATE agents SET is_active = 0")
        c.execute("UPDATE agents SET is_active = 1 WHERE id = ?", (agent_id,))
        
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        conn.commit()
        conn.close()
        return {"status": "success", "active_agent_id": agent_id}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}")
@router.delete("/agents/{agent_id}/remove")
async def delete_agent(agent_id: str):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check active status
        c.execute("SELECT is_active FROM agents WHERE id = ?", (agent_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        is_active = bool(row["is_active"])
        
        # Delete
        c.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        
        # Fail-safe: activate another agent if we just deleted the active one
        if is_active:
            c.execute("SELECT id FROM agents LIMIT 1")
            backup = c.fetchone()
            if backup:
                c.execute("UPDATE agents SET is_active = 1 WHERE id = ?", (backup["id"],))
            else:
                # Re-create default if empty
                new_id = str(uuid.uuid4())
                c.execute("INSERT INTO agents (id, name, system_prompt, model, is_active) VALUES (?, ?, ?, ?, 1)",
                          (new_id, "Grainy Brain", "You are a helpful AI.", "gemma3:latest"))
        
        conn.commit()
        conn.close()
        return {"status": "success", "id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
