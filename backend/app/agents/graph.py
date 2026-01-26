
from langgraph.graph import END, StateGraph
from app.agents.nodes.router import route_question
from app.agents.nodes.grader import grade_documents
from app.agents.nodes.generate import generate, generate_casual
from app.agents.state import GraphState
import chromadb
from app.core.config import settings
from app.core.chroma import get_collection

from app.core.chroma import get_chroma_client

def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]

    # Retrieval
    try:
        from langchain_chroma import Chroma
        from langchain_community.embeddings import OllamaEmbeddings
        
        # Use singleton client
        client = get_chroma_client()
        
        emb_model = OllamaEmbeddings(base_url=settings.OLLAMA_BASE_URL, model=settings.EMBEDDING_MODEL)
        
        print(f"DEBUG: Using Chroma collection: {settings.CHROMA_COLLECTION_NAME}")
        vectorstore = Chroma(
            client=client,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=emb_model,
        )
        
        retriever = vectorstore.as_retriever()
        print(f"DEBUG: Invoking retriever with question: {question}")
        documents = retriever.invoke(question)
        print(f"DEBUG: Retrieved {len(documents)} documents")
        
        return {"documents": documents, "question": question}
    except Exception as e:
        print(f"ERROR in retrieve: {e}")
        import traceback
        traceback.print_exc()
        raise e

def build_graph():
    workflow = StateGraph(GraphState)

    # Define the nodes
    # Remove orphaned router node definition
    # workflow.add_node("router", route_question)
    # Wait, route_question is a conditional edge logic, OR a node that returns the route. 
    # The prompt said "Node: Router ... Returns a JSON action". 
    # In LangGraph, usually we have a START node leading to a conditional edge or a specific node.
    # Let's make "router" a node that just passes state but we use its logic in the conditional edge 
    # OR we use `route_question` function AS the conditional edge logic from START.
    # The prompt says "Node: Router". So let's add it as a node if it modifies state or does work.
    # But `route_question` implementation I wrote returns a string "retrieve" or "generate_casual". 
    # That fits a conditional edge function.
    
    # Let's follow the standard pattern:
    # START -> conditional_edge(route_question) -> "retrieve" or "generate_casual"
    
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("generate_casual", generate_casual)

    # Build the graph
    workflow.set_conditional_entry_point(
        route_question,
        {
            "retrieve": "retrieve",
            "generate_casual": "generate_casual",
        },
    )
    
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_edge("grade_documents", "generate")
    workflow.add_edge("generate", END)
    workflow.add_edge("generate_casual", END)
    
    return workflow.compile()

graph_app = build_graph()
