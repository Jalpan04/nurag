
from fastapi import APIRouter
from app.core.chroma import get_collection
from app.core.config import settings

router = APIRouter()

@router.get("/graph")
async def get_graph_data():
    """
    Returns nodes and links for the 3D/2D force graph.
    Nodes are documents. Links could be semantic similarity.
    """
    collection = get_collection()
    
    # Fetch all data (limit to recent/max for performance if needed)
    # peek() is for preview, get() fetches.
    data = collection.get(include=["metadatas", "documents", "embeddings"]) 
    
    ids = data["ids"]
    metadatas = data["metadatas"]
    # embeddings = data["embeddings"] # Vectors
    
    nodes = []
    links = []
    
    import random
    
    # Construct Nodes
    for idx, doc_id in enumerate(ids):
        # We use a simple structure for the visualizer
        nodes.append({
            "id": doc_id,
            "name": f"Node {doc_id[:8]}", # Or metadata filename if available
            "val": 1 # Size
        })
        
    # Construct Links (Aesthetic Simulation)
    # Since we don't have real semantic links calculated yet, we create a
    # "Constellation" effect where nodes are randomly linked to 1-2 others
    # to demonstrate the frontend capability.
    if len(ids) > 1:
        for i, source_id in enumerate(ids):
            # Link to the next one to form a chain
            target_i = (i + 1) % len(ids)
            links.append({
                "source": source_id,
                "target": ids[target_i]
            })
            # Occasional random cross-link
            if len(ids) > 4 and random.random() > 0.7:
                 random_target = ids[random.randint(0, len(ids)-1)]
                 if random_target != source_id:
                     links.append({
                        "source": source_id,
                        "target": random_target
                    })
    
    return {"nodes": nodes, "links": links}
