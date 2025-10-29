# TasteIQ

> **Personalized restaurant and meal recommendations powered by Retrieval-Augmented Generation (RAG) and fine-tuned LLMs.**

---

## 🧠 Overview

**TasteIQ** is a GenAI-driven system that helps users discover and plan meals based on their preferences, dietary goals, and restaurant availability.

Using a **Retrieval-Augmented Generation (RAG)** pipeline, the system combines:
- **Structured data** from the Spoonacular API (menu items, nutrition, recipes, restaurants)
- **Fine-tuned GPT-3.5 models** for cuisine-specific expertise (e.g. Asian, Mexican, Fast Food)
- **GPT-4o** for reasoning, personalization, and recommendation synthesis  

The result is an intelligent conversational agent that can answer queries like:

> “Find me a vegan fast-food meal under 600 calories.”  
> “Recommend high-protein Mexican dishes for post-workout recovery.”  
> “What’s a balanced dinner option from Chipotle today?”

---

## 🧩 Core Features

| Feature | Description |
|----------|-------------|
| 🍔 **Restaurant-Aware Search** | Integrates with Spoonacular’s restaurant and menu item endpoints to retrieve real fast-food and chain options. |
| 🧬 **Nutrition Intelligence** | Automatically analyzes and ranks meals based on macronutrients, calories, and dietary constraints. |
| 🧠 **RAG-Based Question Answering** | Combines structured nutritional data with GPT reasoning for factual, context-aware answers. |
| 🌍 **Cuisine-Specific Personalization** | Uses fine-tuned GPT-3.5 models per cuisine type for nuanced recommendations. |
| 💬 **Conversational AI Interface** | GPT-4o handles user queries and natural dialogue for a seamless chat experience. |
| ☁️ **Cloud-Native Deployment** | Containerized with Docker and deployable on AWS ECS/Fargate for scalable serving. |

---

## 🧱 Planned Architecture

```plaintext
backend/
├── app.py                    # FastAPI / Flask backend entrypoint
├── api/                      # API routing layer
│   ├── routes.py
│   └── __init__.py
├── services/                 # External service integrations
│   ├── spoonacular_api.py
│   ├── openai_service.py
│   └── __init__.py
├── database/                 # Data ingestion & query logic
│   ├── db.py
│   ├── ingest_data.py
│   └── queries.py
├── rag/                      # RAG pipeline components
│   ├── embeddings.py
│   ├── retriever.py
│   └── pipeline.py
├── fine_tune/                # Fine-tuning scripts & examples
│   ├── prepare_dataset.py
│   ├── upload_and_train.py
│   └── examples/
├── utils/                    # Helper functions
│   ├── preprocess.py
│   └── helpers.py
└── tests/                    # Unit and integration tests
    └── test_api.py
```

## 🔍 System Design

### 1️⃣ Data Layer
- Pulls real-time menu and nutrition data from **Spoonacular API**  
- Normalizes and stores it in a local or cloud database (**SQLite → PostgreSQL/RDS**)  
- Enriches data with embeddings for retrieval (**Weaviate**)

### 2️⃣ RAG Pipeline
- User queries are vectorized and matched against stored embeddings  
- Retrieved context is combined with **GPT-4o** prompt templates  
- GPT synthesizes structured + unstructured information into natural answers

### 3️⃣ Fine-Tuning Layer
- **GPT-3.5** models are fine-tuned per cuisine domain *(Asian, Mexican, Fast Food, etc.)*  
- Fine-tuned models can be dynamically selected based on cuisine classification of the query

### 4️⃣ Deployment Layer
- Packaged via **Docker**  
- Deployable to **AWS ECS/Fargate** or **Lambda (serverless option)**  
- **S3** for data/artifact storage, **CloudWatch** for logs/metrics

---

## 🧮 Example Query Flow

**User:**  
> “I want a low-carb dinner from a fast-food place.”

**RAG Retriever:**  
Fetches relevant menu items from Spoonacular (low-carb tagged)

**GPT-4o Reasoning:**  
Filters by location, taste profile, and dietary rules

**Response:**  
> “Try *Grilled Chicken Salad* from Chick-fil-A — only **8g net carbs** and **320 calories**.”

---

## 🧰 Tech Stack

| Layer | Tools |
|-------|-------|
| **Backend** | Python, FastAPI |
| **Model Serving** | OpenAI GPT-4o, GPT-3.5 fine-tunes |
| **Data Ingestion** | Spoonacular API, Pandas |
| **Database** | SQLite / PostgreSQL (AWS RDS optional) |
| **Vector Store** | Weaviate |
| **Retrieval Augmented Generation** | LlamaIndex |
| **MLOps / Deployment** | Docker, AWS ECS/Fargate, S3, CloudWatch |
| **Version Control** | Git + GitHub Actions (CI/CD planned) |

---

## 🧑‍🍳 Future Enhancements
- 🔁 Continuous fine-tuning pipeline using real user feedback  
- 🏋️ Fitness integration (Fitbit / Apple Health APIs)  
- 🧠 User preference memory for long-term personalization  
- 📊 Evaluation dashboard comparing base GPT-4o vs fine-tuned GPT-3.5 responses  
- 💬 Multi-turn dialogue state management for richer conversations  
- 🧩 LangChain integration for modular orchestration  

---

## 🚀 Deployment Plan

| Stage | Goal |
|--------|------|
| **Phase 1** | Local development, Spoonacular ingestion, simple RAG prototype |
| **Phase 2** | GPT-4o integration + API deployment via FastAPI |
| **Phase 3** | Fine-tune GPT-3.5 models by cuisine type |
| **Phase 4** | Containerize and deploy to AWS ECS (free tier) |
| **Phase 5** | Add automated tests and CI/CD workflow |

---

## 📦 Installation (Planned)

```bash
# Clone the repo
git clone https://github.com/<yourusername>/TasteIQ
cd TasteIQ/backend

# Set up virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run locally
python app.py
