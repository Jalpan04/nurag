# NURAG

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.2-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-FF6F00?style=flat-square)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=flat-square&logo=ollama&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-Personal_Use-green?style=flat-square)

**NURAG** is a local-first, AI-powered Retrieval Augmented Generation (RAG) system with a cyberpunk-inspired industrial interface. It allows you to chat with your documents using locally-hosted LLMs via Ollama.

---

## Features

-   **Local AI**: All processing happens on your machine using [Ollama](https://ollama.ai/). No data leaves your system.
-   **Document Ingestion**: Upload PDFs, HTML, Markdown, Text, and Code files. Documents are chunked, embedded, and stored for semantic retrieval.
-   **Multi-Persona Agents**: Create and switch between different AI personas with custom system prompts and models.
-   **Threaded Conversations**: Chat history is persisted per thread, allowing you to resume conversations.
-   **Industrial UI**: A unique, dark "terminal-style" interface with live graph visualization of your knowledge base.
-   **Fully Dockerized**: Simple one-command deployment.

---

## Tech Stack

| Layer      | Technology                                                                 |
| :--------- | :------------------------------------------------------------------------- |
| **Frontend** | Vanilla HTML, CSS (JetBrains Mono), JavaScript, [Force-Graph](https://github.com/vasturiano/force-graph) |
| **Backend**  | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)                     |
| **Agent Framework** | [LangChain](https://www.langchain.com/) & [LangGraph](https://github.com/langchain-ai/langgraph) |
| **Vector DB** | [ChromaDB](https://www.trychroma.com/)                                   |
| **LLM Engine** | [Ollama](https://ollama.ai/) (Local)                                     |
| **Database** | SQLite (for threads, messages, agents, documents metadata)                 |
| **Containerization** | Docker & Docker Compose                                            |

---

## Prerequisites

1.  **Docker & Docker Compose**: [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
2.  **Ollama**: [Install Ollama](https://ollama.ai/) and ensure it is running on your host machine.
3.  **Required Ollama Models**: Pull the following models:
    ```bash
    ollama pull gemma3:latest
    ollama pull gemma3:1b
    ollama pull nomic-embed-text:latest
    ```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd "rag folder"
```

### 2. Build and Run with Docker Compose

```bash
docker-compose up --build -d
```

This will:
-   Build the backend FastAPI container.
-   Start the frontend static server.
-   Create a persistent volume for ChromaDB.

### 3. Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

The backend API is available at `http://localhost:8000`.

---

## Project Structure

```
rag folder/
|-- backend/
|   |-- app/
|   |   |-- agents/          # LangGraph agent definition (nodes, graph)
|   |   |   |-- nodes/       # Individual graph nodes (retrieve, grade, generate)
|   |   |   |-- graph.py     # Main LangGraph workflow definition
|   |   |-- api/v1/          # FastAPI route handlers
|   |   |   |-- agents.py    # Agent CRUD & selection
|   |   |   |-- chat.py      # Main chat endpoint
|   |   |   |-- documents.py # Document listing & deletion
|   |   |   |-- graph.py     # Knowledge graph data for visualization
|   |   |   |-- ingest.py    # File upload & embedding
|   |   |-- core/            # Configuration (settings, ChromaDB client)
|   |   |-- db/              # SQLite database initialization
|   |   |-- main.py          # FastAPI app entry point
|   |-- Dockerfile
|   |-- requirements.txt
|-- frontend/
|   |-- index.html           # Main UI structure
|   |-- script.js            # All frontend logic
|   |-- style.css            # Industrial/Cyberpunk styling
|   |-- server.js            # Simple Node.js static file server
|-- docker-compose.yml
|-- README.md
```

---

## API Endpoints

All endpoints are prefixed with `/api`.

| Method   | Endpoint                      | Description                               |
| :------- | :---------------------------- | :---------------------------------------- |
| `POST`   | `/chat`                       | Send a query, get an AI response.         |
| `GET`    | `/threads`                    | List all conversation threads.            |
| `DELETE` | `/threads/{thread_id}`        | Delete a thread and its messages.         |
| `POST`   | `/ingest`                     | Upload a file to the knowledge base.      |
| `GET`    | `/documents`                  | List all ingested documents.              |
| `DELETE` | `/documents/{filename}`       | Delete a document from the knowledge base.|
| `GET`    | `/agents`                     | List all AI personas.                     |
| `POST`   | `/agents`                     | Create a new AI persona.                  |
| `PUT`    | `/agents/{agent_id}`          | Update an existing persona.               |
| `DELETE` | `/agents/{agent_id}`          | Delete a persona.                         |
| `POST`   | `/agents/{agent_id}/select`   | Set a persona as the active one.          |
| `GET`    | `/agents/models`              | List available Ollama models.             |
| `GET`    | `/graph`                      | Get node/link data for the knowledge graph.|

---

## Configuration

Environment variables can be set in `docker-compose.yml` or a `.env` file.

| Variable           | Default                            | Description                        |
| :----------------- | :--------------------------------- | :--------------------------------- |
| `OLLAMA_BASE_URL`  | `http://host.docker.internal:11434` | URL to your running Ollama instance. |
| `CHROMA_DB_DIR`    | `/app/chroma_db`                   | Path for ChromaDB persistence.     |

Model selection can be configured in `backend/app/core/config.py`:
-   `CHAT_MODEL`: The main LLM for generation (e.g., `gemma3:latest`).
-   `GRADER_MODEL`: A smaller model for document relevance grading.
-   `EMBEDDING_MODEL`: The model for creating text embeddings (e.g., `nomic-embed-text`).

---

## Supported File Types for Ingestion

-   `.pdf` (Requires `pypdf`)
-   `.html`, `.htm` (Requires `beautifulsoup4`)
-   `.txt`, `.md`
-   Code files: `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.go`, `.rs`, `.rb`, `.php`, `.swift`, `.kt`, `.json`, `.yaml`, `.yml`, `.sh`, `.bat`, `.ps1`, `.css`, `.sql`, `.xml`

---

## License

This project is for personal and educational use.

---

## Acknowledgements

-   [LangChain](https://www.langchain.com/)
-   [Ollama](https://ollama.ai/)
-   [ChromaDB](https://www.trychroma.com/)
-   [Force-Graph](https://github.com/vasturiano/force-graph)
