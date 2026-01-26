from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from pydantic import BaseModel, Field
from app.core.config import settings

class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""
    datasource: Literal["vectorstore", "chat"] = Field(
        ...,
        description="Given a user question choose to route it to 'vectorstore' for retrieval or 'chat' for general conversation."
    )

def route_question(state):
    """
    Route question to vectorstore or chat.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    print("---ROUTE QUESTION---")
    question = state["question"]
    
    # Using qwen2.5-coder for structural output as requested
    print(f"DEBUG: Router configured with base_url: {settings.OLLAMA_BASE_URL}")
    print(f"DEBUG: Router configured with base_url: {settings.OLLAMA_BASE_URL}")
    llm = ChatOllama(model=settings.ROUTER_MODEL, base_url=settings.OLLAMA_BASE_URL, temperature=0, format="json")
    
    from langchain_core.output_parsers import JsonOutputParser
    from langchain_core.prompts import PromptTemplate
    
    parser = JsonOutputParser(pydantic_object=RouteQuery)
    
    prompt = PromptTemplate(
        template="""You are an expert at routing a user question to a vectorstore or casual chat.
The vectorstore contains documents uploaded by the user.
Use the vectorstore for questions on these documents, or if the user asks about specific facts, names, dates, or "my" information (like "what is my name?").
Do not assume you know the answer; if it looks like a lookup, use vectorstore.
Otherwise, use chat.

Return a JSON object with a single key 'datasource' equal to either 'vectorstore' or 'chat'.
Do not return any preamble or explanation.

Question: {question}
""",
        input_variables=["question"],
    )
    
    chain = prompt | llm | parser
    
    try:
        source = chain.invoke({"question": question})
        print(f"DEBUG: Router output: {source}")
        datasource = source.get("datasource", "chat") # Default to chat if parsing fails key check
    except Exception as e:
        print(f"ERROR in router parsing: {e}")
        datasource = "chat"
    
    if datasource == "vectorstore":
        print("---ROUTE QUERY TO RAG---")
        return "retrieve"
    else:
        print("---ROUTE QUERY TO CHAT---")
        return "generate_casual"
