# ManakSetu Architecture

This document outlines the high-level architecture of ManakSetu, our AI-Powered Recommendation Engine for Identifying Applicable Indian Standards.

## System Diagram

```mermaid
graph TD
    %% User Interactions
    User((User)) --> |Accesses| Frontend
    User --> |Uploads Tender PDF| Frontend

    %% Frontend Layer
    subgraph Frontend Layer
        Frontend[Next.js Web Application]
    end

    %% Backend Layer
    subgraph Backend Layer
        API[FastAPI Backend]
        LLM[LLM Service<br>Groq Llama-3]
        DocProcessor[Document Processor<br>PyMuPDF]
        VectorDB[(Qdrant Cloud<br>Vector DB)]
        RelDB[(Supabase<br>PostgreSQL)]
        AIEngine[AI Engine<br>HuggingFace MiniLM]
    end

    %% Flow
    Frontend <--> |REST API Calls| API
    
    %% Internal Backend Logic
    API --> |Sends Text / Gets JSON| LLM
    API --> |Sends PDF / Gets Text| DocProcessor
    API <--> |Queries Metadata| RelDB
    API <--> |Semantic Search| VectorDB
    
    %% AI Engine Interaction
    DocProcessor --> |Extracted Text Chunks| AIEngine
    AIEngine --> |Generates Embeddings| VectorDB
```

## Description of Components

1. **Frontend (Next.js):** The user interface providing search functionality, document upload zones, and standard details.
2. **Backend (FastAPI):** The core API orchestrating all background logic and external connections.
3. **LLM Service (Groq):** Provides high-speed text summarization, conversational interactions, and compliance extraction from documents.
4. **Document Processor:** Extracts clean text from uploaded PDFs/DOCX files.
5. **AI Engine (HuggingFace local model):** Generates 384-dimensional mathematical embeddings from text without requiring external API calls.
6. **Qdrant Vector DB:** Stores and searches the embeddings for extremely fast and accurate semantic matching.
7. **PostgreSQL:** Stores stable relational data, links, and pre-generated AI summaries for Indian Standards.
