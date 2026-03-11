# taskmaster-adk
A production-grade, autonomous AI Task Manager built with Google ADK and FastAPI, featuring structured JSON observability and containerized microservice architecture.
# 🤖 TaskMaster-ADK: Agentic CRUD Microservice

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Google ADK](https://img.shields.io/badge/Google_ADK-1.26.0-4285F4.svg)](https://github.com/google/digital-asset-links)

## 📌 Project Overview
TaskMaster-ADK is a production-grade **Autonomous AI Agent** built using the **Google Agent Development Kit (ADK)**. Transitioning beyond deterministic programming, this system utilizes a "Reason-then-Act" (ReAct) pattern to interpret natural language intent and execute discrete Python-based tools to manage data state.

### 🌟 Key Features
* **Agentic Orchestration:** Uses LLM reasoning to map ambiguous user prompts to validated CRUD operations.
* **Production Observability:** Integrated FastAPI middleware providing structured **JSON logging** and **Correlation ID** tracing for full request-lifecycle visibility.
* **Resilient Design:** Optimized for **Gemini 1.5 Flash** to maintain high Requests-Per-Minute (RPM) and handle API quota limits gracefully.
* **Cloud-Native Architecture:** Fully containerized using **Podman/Docker-Compose** with a focus on non-root security.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Client_Layer [Frontend Layer]
        A[Streamlit UI]
    end

    subgraph API_Layer [Backend Microservice]
        B[FastAPI Gateway]
        C{Observability Middleware}
        D[JSON Logger / Tracing]
    end

    subgraph AI_Orchestration [Agentic Core]
        E[Google ADK Agent]
        F[Gemini 1.5 Flash]
    end

    subgraph Tool_Layer [Data & Tools]
        G[CRUD Toolset]
        H[(Mock DB / Task Store)]
    end

    A -->|User Prompt| B
    B --> C
    C -->|Generate Request ID| D
    C -->|Contextual Prompt| E
    E <-->|Inference| F
    E -->|Invoke Tool| G
    G <-->|State Change| H
    G -->|Execution Result| E
    E -->|Final Response| B
    B -->|JSON Response| A
