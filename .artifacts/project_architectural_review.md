# AI Agent Bazi Workflow & Telegram Bot: Architectural Review

## 1. Project Overview

This project is a high-performance Telegram Bot built in **Rust** that provides professional Chinese Daily Almanac (黄历) and Bazi (八字) fortune-telling analysis.

Instead of relying solely on hardcoded logic, it intelligently retrieves traditional calendar data via an API, formats it, and orchestrates requests to an **LLM service (specifically AI Agent AI)** using specialized prompts to generate sophisticated "Blindman Bazi" (盲派命理) Chain of Thought analysis.

## 2. Core Architecture Stack

- **Bot Framework**: `teloxide` for the Telegram Bot API and routing.
- **Async Runtime**: `tokio` (multi-threaded async reactor).
- **HTTP/Networking**: `reqwest` (for making external API calls) & `async-openai` (interacting with AI Agent/LLM endpoints via the OpenAI compatible standard).
- **Memory/State**: `dashmap` for lock-free, concurrent in-memory session storing.
- **Persistence**: `sqlx` driving SQLite, to save local user requests and individual birth dates.
- **Scheduling Tasks**: `tokio-cron-scheduler` for daily background jobs and garbage collection.

## 3. Overall Flow & Component Breakdown

The `src/` directory holds the monolithic codebase where several distinct modules act iteratively:

### 3.1 Initializing & Routing (`src/main.rs` & `src/handlers.rs`)

- `main.rs` seeds the `AppState` which holds the internal SQLite connection pool, HTTP client, and concurrency maps.
- Using `dptree`, `teloxide`'s dispatching mechanism intercepts:
  - Text messages.
  - Commands (`/start` and `/new`).
  - Callback queries (when the user clicks the inline Calendar UI).

### 3.2 Display & Input UI (`src/calendar.rs`)

- Contains logic for inline Telegram keyboards.
- Drives users through step-by-step inputs (Year/Month -> Day -> Hour -> Minute) for their birthtime without typing constraints, improving UX layout strictly via callback data buttons.

### 3.3 State & DB Layer (`src/state.rs` & `src/db.rs`)

- `AppState` securely retains user conversations globally in `user_contexts` (`DashMap`) capped at recent interactions up to 10 messages.
- It tracks `user_last_active` to groom out stale sessions.
- `db.rs` writes down analytics, selected days, text queries, responses, and user profiles directly using raw async SQLite statements.

### 3.4 Data Retrieval & Parsing (`src/almanac.rs`)

- Fetches raw almanac data from an external provider (`mingdecode.com`).
- Applies a schema mapping (filtering out unnecessary bloated keys), recursively maps English generic JSON keys to traditional Chinese schema labels (e.g., `jiShen` -> `吉神宜趋`), and actively injects the "Kong Wang" (空亡) computation manually into the payload map so the LLM remains accurate.

### 3.5 AI Integration (`src/llm_bazi.rs`)

- Employs `async_openai` to package the user's base Bazi facts, the retrieved `almanac` string, previous context interactions, and the `BaziHuangLiAssistantPrompt.md` template.
- Although it relies on OpenAI protocols, it's designed to override its `api_base` configurations to point at AI Agent workflows.

### 3.6 Autonomous Tasks (`src/scheduler.rs`)

- Starts two robust repeating jobs:
  1. A Cleanup Cron (`0 */5 * * * *`) that sweeps through global dicts, wiping users inactive past a certain interval config.
  2. A Daily Aggregation Cron (`0 0 14 * * *` standard time / 10 PM SGT) querying tomorrow's date, bypassing human prompts, and delivering the Bazi report unilaterally back to an admin chat.

## 4. Important Documentation Files

- **`README.md`**: Provides the top-level introduction, key features, local `.env` requirements, and building commands.
- **`BaziHuangLiAssistantPrompt.md`**: The system instruction manual passed onto AI Agent AI. Constrains the model entirely around specific Bazi interpretation constraints prioritizing "体用" & "做功" mechanics over generic approaches.
- **`DEPLOYMENT.md`**: Crucial context specifying how to run this on an ARM device like Raspberry Pi under DietPi OS using cross-compilation target mappings alongside background execution via daemons.
- **`telegramBot.service`**: The pre-configured Systemd deployment unit file.
- **`Cargo.toml`**: The canonical reference for external dependencies and entry execution rules.

## 5. Directory Structure

```text
AI AgentBaziWorkflow/
├── .env                       # App secrets (Telegram token, API endpoints/keys)
├── Cargo.toml                 # Cargo config and dep tree
├── DEPLOYMENT.md              # Raspberry Pi/Linux daemon instructions
├── BaziHuangLiAssistantPrompt.md # System prompt config mapped centrally
├── telegramBot.service        # Systemd daemon config helper
├── src/                       # Rust source entry
│   ├── main.rs                # Setup + entry
│   ├── handlers.rs            # Handle user interaction events
│   ├── state.rs               # Shared memory representation struct
│   ├── calendar.rs            # Telegram inline ui bindings
│   ├── db.rs                  # Sqlx DB routines for SQLite
│   ├── almanac.rs             # Almanac parsing & api routines
│   ├── llm_bazi.rs            # OpenAI wrapping and AI Agent calling
│   └── scheduler.rs           # Cron schedules mapping
└── py_src/                    # Legacy python version folder architecture
```
