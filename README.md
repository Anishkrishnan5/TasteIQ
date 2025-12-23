TasteIQ

Personalized restaurant and meal recommendations powered by Retrieval-Augmented Generation (RAG).

🧠 Overview

TasteIQ is a GenAI-driven system that helps users discover and plan meals based on their preferences, dietary goals, and restaurant availability.

Using a Retrieval-Augmented Generation (RAG) pipeline, the system grounds LLM responses in structured nutrition and menu data, enabling accurate, constraint-aware recommendations rather than free-form hallucinations.

Using a RAG-based architecture, TasteIQ combines:

Structured data from the Spoonacular API (menu items, nutrition, recipes, restaurants)

Semantic retrieval over embedded menu items for relevant context selection

GPT-4o for reasoning, personalization, and recommendation synthesis

Cuisine-aware prompt routing for nuanced recommendation styles (e.g. Asian, Mexican, Fast Food)

The result is an intelligent conversational agent that can answer queries like:

“Find me a vegan fast-food meal under 600 calories.”
“Recommend high-protein Mexican dishes for post-workout recovery.”
“What’s a balanced dinner option from Chipotle today?”

💡 Why This Matters

Modern food discovery tools are limited to static filters or crowd-sourced ratings, which struggle to handle multiple simultaneous constraints such as nutrition targets, dietary rules, and personal preferences.

TasteIQ moves beyond this by combining nutritional intelligence, semantic retrieval, and LLM-based reasoning to produce grounded, personalized recommendations.

It represents how applied GenAI systems bridge structured data (menus, nutrition) with LLM-driven decision-making — an approach increasingly used across real-world recommender systems, digital health platforms, and consumer AI products.

🧩 Core Features
Feature	Description
🍔 Restaurant-Aware Search	Integrates with Spoonacular’s restaurant and menu item endpoints to retrieve real fast-food and chain options.
🧬 Nutrition Intelligence	Automatically analyzes and ranks meals based on macronutrients, calories, and dietary constraints.
🧠 RAG-Based Question Answering	Uses semantic retrieval to ground LLM responses in factual nutrition and menu data.
🌍 Cuisine-Aware Personalization	Routes queries to cuisine-specific prompt templates for contextually appropriate recommendations.
💬 Conversational AI Interface	GPT-4o handles multi-constraint reasoning and natural dialogue.
☁️ Cloud-Native Deployment	Containerized with Docker and deployable on AWS ECS/Fargate for scalable serving.
🧱 Planned Architecture
backend/
├── app.py                    # FastAPI backend entrypoint
├── api/                      # API routing layer
│   ├── routes.py
│   └── __init__.py
├── services/                 # External service integrations
│   ├── spoonacular_api.py
│   ├── llm_service.py
│   └── __init__.py
├── database/                 # Data ingestion & query logic
│   ├── db.py
│   ├── ingest_data.py
│   └── queries.py
├── rag/                      # RAG pipeline components
│   ├── embeddings.py
│   ├── retriever.py
│   └── pipeline.py
├── evaluation/               # Retrieval + response evaluation
│   ├── metrics.py
│   └── benchmarks.py
├── utils/                    # Helper functions
│   ├── preprocess.py
│   └── helpers.py
└── tests/                    # Unit and integration tests
    └── test_api.py

🔍 System Design
1️⃣ Data Layer

Pulls real-time menu and nutrition data from the Spoonacular API

Normalizes and stores data in a local or cloud database (SQLite → PostgreSQL/RDS)

Enriches menu items with embeddings for semantic retrieval (Weaviate)

2️⃣ RAG Pipeline

User queries are embedded and matched against stored menu embeddings

Top-k retrieved menu items are injected into GPT-4o prompt templates

GPT synthesizes responses grounded in retrieved nutritional context

This design significantly reduces hallucinated nutrition facts compared to a prompt-only LLM baseline.

3️⃣ Personalization & Model Strategy

Uses prompt routing based on inferred cuisine and dietary intent

Explores lightweight fine-tuning and prompt variants as an experimental comparison, not a core dependency

Prioritizes retrieval quality and prompt structure over heavy model specialization

4️⃣ Deployment Layer

Packaged via Docker for reproducible builds

Deployable to AWS ECS/Fargate or Lambda (serverless option)

S3 for data/artifact storage, CloudWatch for logs and metrics

🧮 Example Query Flow

User:

“I want a low-carb dinner from a fast-food place.”

RAG Retriever:
Fetches relevant low-carb menu items from Spoonacular embeddings

GPT-4o Reasoning:
Applies dietary constraints, ranking logic, and preference filters

Response:

“Try Grilled Chicken Salad from Chick-fil-A — approximately 8g net carbs and 320 calories.”

🧰 Tech Stack
Layer	Tools
Backend	Python, FastAPI
Model Serving	OpenAI GPT-4o
Data Ingestion	Spoonacular API, Pandas
Database	SQLite / PostgreSQL
Vector Store	Weaviate
Retrieval Augmented Generation	LlamaIndex
MLOps / Deployment	Docker, AWS ECS/Fargate, S3, CloudWatch
Version Control	Git + GitHub Actions
🧑‍🍳 Future Enhancements

🤖 Agent-based extensions (restaurant lookup, ordering workflows)

🧠 Long-term user preference memory

📊 Expanded evaluation dashboard for retrieval quality and response correctness

💬 Improved multi-turn dialogue state tracking

🚀 Deployment Plan
Stage	Goal
Phase 1	Local development, Spoonacular ingestion, RAG prototype
Phase 2	GPT-4o integration + API deployment via FastAPI
Phase 3	Evaluation pipeline and prompt routing
Phase 4	Containerize and deploy to AWS ECS
Phase 5	Add automated tests and CI/CD workflow
📦 Installation (Planned)
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
