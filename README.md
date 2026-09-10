# ManakSetu - Indian Standards AI

This repository contains the source code for our submission to the Smart India Hackathon (SIH) 2026.

## 1. Project Information

- **Project Title:** ManakSetu
- **PS ID:** SIH26108
- **PS Title:** AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications
- **Category:** Software
- **Theme:** Smart Automation / Smart Governance

## 2. Problem Statement

Organizations and procurement divisions struggle to identify the correct and most up-to-date Indian Standards (IS) for complex technical procurement specifications. Sifting through hundreds of pages of unstructured technical documents and relying on traditional keyword searches often leads to critical compliance gaps, outdated information, and procurement delays.

## 3. Proposed Solution

ManakSetu is an end-to-end AI-powered procurement assistant designed to perform semantic retrieval, requirement mapping, and compliance analysis. Users can upload raw tender specifications or provide natural language descriptions. The system extracts technical parameters, translates them into high-dimensional semantic vectors using a local HuggingFace MiniLM model, and queries a Qdrant database to identify the precise normative and allied Indian Standards. It is built entirely on open-source technologies, ensuring security and zero-cost local inferencing.

## 4. Key Features

- **Tender-as-a-Query & Semantic Discovery:** Replaces rigid keyword matching with meaning-based retrieval, instantly scanning the repository to find primary and allied standards based on complex technical requirements.
- **Traceable Conversational Assistant:** Features a 'Chat with Document' widget powered by a Grounded RAG pipeline, providing expert answers linked directly to source clauses.
- **Automated AI Summaries:** Generates precise 3-to-4 bullet point executive summaries of complex Indian Standards.
- **Explainable Compliance Validation:** Surfaces requirement-standard gaps, conflicts, and risks using an LLM-assisted compliance audit.

## 5. Technology Stack

- **Frontend:** Next.js (React, TypeScript), Tailwind CSS, GSAP
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy
- **Databases:** PostgreSQL (Relational Metadata), Qdrant (Vector Database)
- **AI/ML:** HuggingFace `sentence-transformers` (MiniLM embeddings), Groq API (qwen-3.6-27b), PyMuPDF
- **Infrastructure:** Docker, Docker Compose

## 6. Architecture

See [docs/architecture.md](docs/architecture.md).

```text
User
  |
  v
Frontend (Next.js)
  |
  +----> LLM Chat/Summary (Groq Llama-3)
  |
  v
Backend API (FastAPI)
  |
  +----> PostgreSQL (Metadata)
  |
  +----> Qdrant (Vector Embeddings)
  |
  v
HuggingFace MiniLM (Local Inference)
```

## 7. Repository Structure

```text
ManakSetu/
├── README.md
├── SUBMISSION_GUIDE.md
├── submission/
│   ├── PRESENTATION.md
│   └── DEMO.md
├── backend/          # Python FastAPI backend & AI Engine
├── frontend/         # Next.js web application
├── docs/
│   └── architecture.md
├── assets/
│   └── screenshots/
└── indian_standards_cleaned.csv  # Dataset
```

## 8. Team Members
- **Manish:** Data arrangement
- **Anuj Biswas:** AI architect
- **Aryan Anand:** Backend architect
- **Vishesh Shokeen:** Frontend developer
- **Deepanshu Solanki:** Frontend developer
- **Hitansha Pandey:** PPT / Presentation
