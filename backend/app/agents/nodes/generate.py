from app.core.config import settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.db.db import get_db_connection

def get_active_agent_prompt():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT system_prompt, model FROM agents WHERE is_active = 1")
        row = c.fetchone()
        conn.close()
        if row:
            return row["system_prompt"], row["model"]
    except:
        pass
    # Default
    return ("You are 'Grainy Brain', a helpful, witty, and concise AI assistant. Answer naturally and conversationally.", "gemma3:latest")

def generate(state):
    """
    Generate answer
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    # Get active persona
    persona_prompt, model_name = get_active_agent_prompt()
    
    # RAG generation
    llm = ChatOllama(model=model_name, base_url=settings.OLLAMA_BASE_URL, temperature=0)
    
    # Format docs
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    context = format_docs(documents)
    
    prompt = f"""{persona_prompt}
    
    IMPORTANT RULES:
    1. Answer NATURALLY, based on the context provided below.
    2. If the answer is not in the context, just say you don't know.
    3. Keep the answer concise.
    
    Context: {context}
    
    Question: {question}
    
    Answer:"""
    
    # Using StrOutputParser for simple string generation
    # invoke takes a list of messages or a string prompt
    
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    
    return {"documents": documents, "question": question, "generation": response.content}

def generate_casual(state):
    """
    Generate casual conversation answer (No RAG)

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE CASUAL---")
    question = state["question"]
    
    # Get active persona logic
    persona_prompt, model_name = get_active_agent_prompt()
    
    # Use the active model and prompt
    llm = ChatOllama(model=model_name, base_url=settings.OLLAMA_BASE_URL, temperature=0.7)
    
    # Construct messages with active persona
    messages = [SystemMessage(content=persona_prompt), HumanMessage(content=question)]
    response = llm.invoke(messages)
    
    return {"question": question, "generation": response.content}
