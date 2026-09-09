# ManakSetu - Indian Standards AI

This repository contains the source code for our submission to the Smart India Hackathon (SIH) 2026.

## 1. Project Information

- **Project Title:** ManakSetu
- **PS ID:** SIH26108
- **PS Title:** AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications
- **Category:** Software
- **Theme:** Smart Automation / Smart Governance

## 2. Problem Statement

Organizations and procurement divisions struggle to accurately identify the applicable Indian Standards (IS) for complex technical procurement specifications. The manual process is extremely slow, error-prone, and relies heavily on domain experts parsing through hundreds of dense PDF documents to find the correct specifications and certification requirements.

## 3. Proposed Solution

ManakSetu is an end-to-end AI-powered recommendation engine. Users can either perform intelligent semantic searches for specific materials/processes, or upload an entire procurement/tender document. Our system automatically extracts the text using OCR, generates vector embeddings, and performs a semantic search against the official Bureau of Indian Standards (BIS) database to instantly recommend all applicable standards, complete with an AI-generated compliance analysis.

## 4. Key Features

- **Semantic Standard Search:** Search for standards using natural language, powered by HuggingFace vector embeddings.
- **Tender Document Analysis:** Upload full PDF/DOCX procurement documents to automatically extract and map required IS codes.
- **AI Chat with Standards:** Users can directly chat with the dense text of any standard to get immediate answers to complex engineering or compliance questions.
- **Automated AI Summaries:** Generates 3-4 bullet point summaries for dense technical standards.
- **Fast & Intuitive UI:** Modern Next.js interface providing an excellent user experience.

## 5. Technology Stack

- **Frontend:** Next.js (React), TailwindCSS
- **Backend:** Python, FastAPI
- **AI & ML:** HuggingFace `sentence-transformers`, Groq Cloud (Llama 3 LLM)
- **Vector Database:** Qdrant Cloud
- **Relational Database:** PostgreSQL (Supabase)
- **Deployment:** Vercel (Frontend), Render (Backend), Docker

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
