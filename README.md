# TasteIQ

> **Personalized restaurant and meal recommendations powered by Retrieval-Augmented Generation (RAG) and fine-tuned LLMs.**

---

## 🧠 Overview

**Tiberius Eats** is a GenAI-driven system that helps users discover and plan meals based on their preferences, dietary goals, and restaurant availability.

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
