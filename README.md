# Squabblin' 'bout Goblins

An open-source monorepo built by a cross-functional team to demonstrate production-grade data engineering, NLP, and agentic AI skills — through projects worth actually using.

---

## 📖 Start Here → [Project Wiki](https://github.com/Squabblin-bout-goblins/squabblin-goblins/wiki)

The wiki is the source of truth for this repo. If you're new, that's where to go first.

---

## Projects

### 🏈 Fantasy Football Intelligence
Scrapes articles, beat writer coverage, and ADP data. Integrates with the [Sleeper API](https://docs.sleeper.com/) for live league context — your actual roster, available players, league settings. Surfaces insight through a dashboard and a natural language draft co-pilot. Every recommendation is logged and scored against real NFL outcomes a week later.

→ [Wiki: Fantasy Football](https://github.com/Squabblin-bout-goblins/squabblin-goblins/wiki/Fantasy-Football)

### 🃏 MTG Market Insights
Tracks Magic: The Gathering card prices via the TCGPlayer and eBay APIs, with card and format metadata from Scryfall. Goes beyond price reporting — the agent reasons about *why* a card moved (bans, reprints, meta shifts, tournament results) and evaluates whether that reasoning held up against the actual price move.

→ [Wiki: MTG Market Insights](https://github.com/Squabblin-bout-goblins/squabblin-goblins/wiki/MTG-Market-Insights)

---

## Shared Architecture Pattern

Both projects follow the same six-layer pipeline: **Ingest → Clean → Enrich → Store → Orchestrate → Serve**, and share the same core stack.

| Layer | Tool |
|---|---|
| Scraping | Playwright |
| Storage | Postgres + pgvector, Neo4j (Docker) |
| Orchestration | Prefect |
| NLP / Embeddings | HuggingFace (local) |
| Dashboard | Streamlit |
| Agents | LangGraph |
| Hosting | HuggingFace Spaces |
| Source Control | GitHub |

Full architecture details live on the [wiki Home page](https://github.com/Squabblin-bout-goblins/squabblin-goblins/wiki).

---

## Articles

We document what we build. Articles linked here as published.

---

## License

MIT
