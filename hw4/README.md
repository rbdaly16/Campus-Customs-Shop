# Campus Customs: HW 4

A Yale-blue storefront for **Campus Customs** (officially licensed Yale apparel, 57 Broadway, New Haven) with **"Ask Dan,"** a PydanticAI shopping assistant. Dan answers questions about real stock and prices from the shop database, puts search results on the page as product cards, remembers logged-in customers, and follows your cursor as a cartoon Handsome Dan.

- **Frontend:** React + Vite + TypeScript (`frontend/`), on port 5175
- **Backend:** FastAPI (`backend/main.py`), on port 8000
- **Agent:** PydanticAI with `gpt5.6-luna` via Portkey. It's four files in `backend/`:

| File | What it is |
|---|---|
| [`backend/prompts/prompt.md`](backend/prompts/prompt.md) | System prompt: voice, how to answer, safety rules |
| [`backend/agent.py`](backend/agent.py) | Agent wiring: model, tools, dynamic context, price fact-check guard, loop limits, audit |
| [`backend/tools.py`](backend/tools.py) | Read-only tools: search, product info, stock, similar items, account, past chats |
| [`backend/models.py`](backend/models.py) | Pydantic types for tool results, agent output, chat API, deps |

The full system description (every model field, tool, safety rule, and limit) is in [`output/harness.md`](output/harness.md).

---

## 1. Place the data pack

The database and product photos are **not** in this repo. Unzip the data pack into this folder so you get:

```
hw4/
└── data/
    ├── campus_customs.db      # SQLite: catalogue, inventory, users, chat_messages
    └── products/              # 102 product photos (*.jpg)
```

For example, from inside `hw4/`:

```bash
unzip ~/Downloads/data.zip -d .
```

Check that `data/campus_customs.db` and `data/products/` both exist. `data/` is gitignored.

## 2. Configure secrets

```bash
cp .env.example .env
```

Edit `.env` and set:
- `PORTKEY_API_KEY`: your Portkey key.
- `SESSION_SECRET`: any long random string, e.g. `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.

`.env` is gitignored.

## 3. Run the backend (FastAPI + agent)

Needs Python 3.11+. From `hw4/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Check it at http://127.0.0.1:8000/api/products, which should list 102 products. Interactive API docs are at http://127.0.0.1:8000/docs.

## 4. Run the frontend (React + Vite)

Needs Node 20+. In a second terminal, from `hw4/`:

```bash
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5175**. Vite proxies `/api` and `/images` to the backend on port 8000, so start the backend first.

## 5. Try it

- **Browse:** Products has search, category chips, an "in stock in my size" filter, and sorting.
- **Ask Dan** (bottom-right):
  - On a product page, ask *"Do you have this in XL?"* for honest stock from the database.
  - Ask *"What hoodies do you have?"* and all 27 appear on the Products page as cards.
  - Ask *"It's sold out in my size, anything similar?"* for in-stock alternatives.
- **Accounts:** create one, or log in with the seed test user from the assignment. Logged-in chats are saved and reload next visit. Guests can chat too, but nothing is saved.
- **Handsome Dan** follows a mouse cursor, licks or grins on click, and spins when idle. Turn him off in the footer.

## 6. Checks (from `backend/`, with the venv active)

```bash
python test_price_guard.py                         # scripted model, no API calls: stale $65 is rejected, reply says $72
python bench_agent.py --efforts default --repeats 1   # live: 6 questions graded against the database
```

## What's in `output/`

| File | Contents |
|---|---|
| [`harness.md`](output/harness.md) | How the system works: models, tools, safety rules, specs and limits, audit trail |
| [`app_check.html`](output/app_check.html) | Live-site test report with screenshots (double-click to open) |
| [`usability.md`](output/usability.md) | Problem 9 improvements and why they help |
| [`design.md`](output/design.md) | Problem 10 storefront design and why it helps |
| `audit_trail.json` | Append-only log of agent activity: tool calls, results, stop reasons. The app adds to it as it runs. |
| `screenshots/`, `app_check_images/` | Evidence screenshots |

The prompt log for every problem is in [`AI_prompts.md`](AI_prompts.md).

## Not in this repo (by design)

- `.env`: real secrets. Use `.env.example`.
- `data/campus_customs.db` and `data/products/`: the data pack, placed locally (step 1).
- `.venv/`, `node_modules/`, `dist/`: rebuilt by the commands above.
