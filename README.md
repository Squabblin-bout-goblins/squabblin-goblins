# Squabblin' 'bout Goblins

An open-source fantasy football intelligence platform built by a cross-functional team to demonstrate production-grade data engineering, NLP, and agentic AI skills.

Scrapes articles, beat writer coverage, and ADP data. Integrates directly with the [Sleeper API](https://docs.sleeper.com/) for live league context — your actual roster, available players, and league settings. Surfaces everything through an interactive dashboard and a natural language draft co-pilot.

---

## 📖 Start Here → [Project Wiki](https://github.com/Squabblin-bout-goblins/squabblin-goblins/wiki)

The wiki is the source of truth for this project. If you're new, that's where to go first. It covers:

- Full architecture overview — how data flows from scrape to insight
- RAG strategy — dense retrieval vs. GraphRAG and when each wins
- Hindsight evaluation — how we score agent recommendations against real outcomes
- Setup guide — every tool you need, how to install it, and the gotchas
- Schema design, agent architecture, and more

---

## What It Does

- **Scrapes** articles, rankings, and ADP data at scale (Playwright)
- **Cleans and enriches** raw text into structured intelligence (HuggingFace NLP)
- **Stores** structured data and embeddings (Postgres + pgvector) and relationships (Neo4j)
- **Orchestrates** pipelines on a schedule with retries and observability (Prefect)
- **Answers questions** in natural language via an AI agent that knows your actual league (LangGraph + Sleeper API)
- **Dashboards** trends, ADP movement, and retrieval comparisons (Streamlit)
- **Evaluates itself** — every recommendation is logged and scored against real NFL outcomes one week later

---

## Tech Stack

| Layer | Tool |
|---|---|
| Scraping | Playwright |
| Storage | Postgres + pgvector, Neo4j (Docker) |
| Orchestration | Prefect |
| NLP / Embeddings | HuggingFace (local) |
| Dashboard | Streamlit |
| Agents | LangGraph |
| League Integration | Sleeper API |
| Hosting | HuggingFace Spaces |
| Source Control | GitHub |

---

## Articles

We document what we build. Articles linked here as published.

---

## License

MIT
