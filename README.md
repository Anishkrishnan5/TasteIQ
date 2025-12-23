# TasteIQ

**Personalized restaurant and meal recommendations powered by Retrieval-Augmented Generation (RAG).**

---

## 🧠 Overview

TasteIQ is a GenAI-driven system that helps users discover and plan meals based on their preferences, dietary goals, and restaurant availability.

Using a **Retrieval-Augmented Generation (RAG)** pipeline, the system grounds LLM responses in structured nutrition and menu data, enabling accurate, constraint-aware recommendations rather than free-form hallucinations.

TasteIQ combines:

- Structured data from the **Spoonacular API**
- Semantic retrieval over embedded menu items
- **GPT-4o** for reasoning and recommendation synthesis
- Cuisine-aware prompt routing for contextual personalization

---

## 💡 Why This Matters

Traditional food discovery tools rely on static filters or ratings, which struggle to handle complex combinations of nutrition goals, dietary rules, and personal preferences.

TasteIQ demonstrates how **RAG-based GenAI systems** can bridge structured data with LLM reasoning to deliver grounded, personalized recommendations — an approach increasingly used in consumer AI and digital health platforms.

---

## 🧩 Core Features

| Feature | Description |
|------|------------|
| 🍔 Restaurant-Aware Search | Retrieves real menu items from Spoonacular |
| 🧬 Nutrition Intelligence | Ranks meals by calories, macros, and constraints |
| 🧠 RAG-Based QA | Grounds LLM responses in factual menu data |
| 🌍 Cuisine-Aware Personalization | Cuisine-specific prompt routing |
| 💬 Conversational Interface | Multi-constraint reasoning via GPT-4o |
| ☁️ Cloud-Native Deployment | Dockerized and deployable on AWS |

---

## 🧱 Planned Architecture

> **Codebase-level view of the system**

```text
backend/
├── app.py                    # FastAPI entrypoint
├── api/                      # API routing
│   ├── routes.py
│   └── __init__.py
├── services/                 # External integrations
│   ├── spoonacular_api.py
│   ├── llm_service.py
│   └── __init__.py
├── database/                 # Data ingestion & queries
│   ├── db.py
│   ├── ingest_data.py
│   └── queries.py
├── rag/                      # RAG pipeline
│   ├── embeddings.py
│   ├── retriever.py
│   └── pipeline.py
├── evaluation/               # Retrieval + response eval
│   ├── metrics.py
│   └── benchmarks.py
├── utils/
│   ├── preprocess.py
│   └── helpers.py
└── tests/
    └── test_api.py
```

---

## 🔍 System Design

_End-to-end system behavior and data flow_

### 1️⃣ Data Layer

- Pulls menu and nutrition data from **Spoonacular**
- Normalizes and stores data (**SQLite → PostgreSQL / RDS**)
- Generates embeddings for semantic retrieval (**Weaviate**)

### 2️⃣ RAG Pipeline

- User queries are embedded
- Top-k relevant menu items are retrieved via vector search
- Retrieved context is injected into **GPT-4o** prompts
- Responses are grounded in factual nutrition data

### 3️⃣ Personalization Strategy

- Prompt routing based on inferred cuisine and dietary intent
- Lightweight fine-tuning explored experimentally
- Emphasis on retrieval quality over model specialization

### 4️⃣ Deployment Layer

- Dockerized backend
- Deployable via **AWS ECS / Fargate** or **Lambda**
- **S3** for artifacts, **CloudWatch** for logging

---

## 🧮 Example Query Flow

### **User**
I want a low-carb dinner from a fast-food place.

markdown
Copy code

### **Retriever**
Fetches low-carb menu items via vector search

markdown
Copy code

### **LLM Reasoning**
Applies dietary constraints and ranking logic

markdown
Copy code

### **Response**
Try Grilled Chicken Salad from Chick-fil-A — ~8g net carbs, 320 calories.

yaml
Copy code

---

## 🧰 Tech Stack

| Layer | Tools |
|------|------|
| Backend | Python, FastAPI |
| LLM | OpenAI GPT-4o |
| Data | Spoonacular API, Pandas |
| Database | SQLite / PostgreSQL |
| Vector Store | Weaviate |
| RAG | LlamaIndex |
| Deployment | Docker, AWS ECS/Fargate |
| CI/CD | GitHub Actions |

---

## 🧑‍🍳 Future Enhancements

- Agent-based workflows (ordering, restaurant lookup)
- Long-term user preference memory
- Evaluation dashboard for retrieval quality
- Improved multi-turn dialogue state tracking

---

## 🚀 Deployment Plan

| Phase | Goal |
|------|-----|
| Phase 1 | Local RAG prototype |
| Phase 2 | FastAPI + GPT-4o integration |
| Phase 3 | Evaluation pipeline |
| Phase 4 | AWS deployment |
| Phase 5 | CI/CD + testing |

---

## 📦 Installation (Planned)

```bash
git clone https://github.com/<yourusername>/TasteIQ
cd TasteIQ/backend

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

python app.py

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python app.py
