from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from pydantic import BaseModel, Field
from app.core.config import settings
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    
    # Score each doc
    filtered_docs = []
    
    llm = ChatOllama(model=settings.GRADER_MODEL, base_url=settings.OLLAMA_BASE_URL, temperature=0, format="json")
    
    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
        Here is the retrieved document: \n\n {document} \n\n
        Here is the user question: {question} \n
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.
        Return a JSON object with a single key 'binary_score' and no preamble or explanation.
        """,
        input_variables=["question", "document"],
    )
    
    parser = JsonOutputParser(pydantic_object=GradeDocuments)
    chain = prompt | llm | parser
    
    for d in documents:
        try:
            score = chain.invoke({"question": question, "document": d.page_content})
            grade = score.get("binary_score", "no")
        except Exception as e:
            print(f"Grade error: {e}")
            grade = "no"
            
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
            
    return {"documents": filtered_docs, "question": question}
