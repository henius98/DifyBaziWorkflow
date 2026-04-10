# AI Bazi Telegram Bot Agent: AI Developer Context

This file serves as a quick-start index for AI agents (like Cursor, Windsurf, or Copilot) to understand the project structure and context immediately, saving tokens and indexing time.

**Core Rule:** DO NOT REMOVE USER COMMENTS DURING EDITS. (`<RULE[user_global]>`)

---

## 🌐 Project Overview

A high-performance Telegram Bot built in **Rust** providing professional Chinese Daily Almanac (黄历) and Bazi (八字) fortune-telling analysis. Instead of relying solely on hardcoded logic, it intelligently retrieves traditional calendar data via an external API, formats it, and orchestrates requests to an **LLM service (AI Agent — via OpenAI-compatible endpoints)** using specialized "Blindman Bazi" (盲派命理) prompts to generate Chain-of-Thought (CoT) analysis.

---

## 🛠 Tech Stack Overview

| Layer         | Library                                 | Purpose                                     |
| ------------- | --------------------------------------- | ------------------------------------------- |
| Bot Framework | `teloxide` (macros enabled)             | Telegram Bot API & routing via `dptree`     |
| Async Runtime | `tokio` (full features)                 | Multi-threaded async reactor                |
| HTTP Client   | `reqwest`, `async-openai`               | External APIs & OpenAI-compatible LLM calls |
| Database      | `sqlx` (SQLite, `runtime-tokio-rustls`) | Persist users, sessions, and requests       |
| Concurrency   | `dashmap`                               | Lock-free in-memory user session state      |
| Scheduling    | `tokio-cron-scheduler`                  | Daily almanac pulls & session GC            |
| Time          | `chrono`, `chrono-tz`                   | Timezone-aware date handling (SGT/UTC+8)    |
| Logging       | `tracing`, `tracing-subscriber`         | Structured async-safe logging               |
| Serialization | `serde`, `serde_json`                   | JSON parsing for API payloads               |

---

## 📂 Source Code Map (`src/`)

- **`main.rs`**: Entry point. Loads `AppConfig` from env, sets up the SQLite pool, creates the `reqwest` HTTP client, builds `AppState`, registers Telegram handlers (commands, callbacks, messages) via `dptree`, and starts the scheduler.
- **`config.rs`**: Reads and validates all configuration from `.env` via `dotenvy`. Single source of truth for secrets and tunables.
- **`state.rs`**: `AppState` struct — shared across all handlers via `Arc`. Holds the HTTP client, SQLite pool, LLM credentials, default user Bazi, and two `DashMap`s (`user_contexts`, `user_last_active`).
- **`handlers.rs`**: All Telegram event handlers — `/start` (date calendar), `/new` (birthdate + time picker), callback queries (calendar navigation + date selection + time selection), and freetext messages.
- **`db.rs`**: Database abstraction layer using `sqlx`. Handles user profiles, interaction logs, request telemetry, and per-user Bazi storage. Migrations live in `./migrations/`.
- **`almanac.rs`**: Fetches raw calendar data from MingDecode API, applies a schema filter (keeping only relevant fields), recursively translates English JSON keys to Chinese labels, and computes "Kong Wang" (空亡) before returning clean plaintext for the LLM.
- **`llm_bazi.rs`**: Packages almanac data + user Bazi + conversation history + system prompt (`BaziHuangLiAssistantPrompt.md`) and calls the LLM via `async-openai` with LLM API base override.
- **`calendar.rs`**: Generates dynamic inline Telegram keyboard calendars and step-by-step time pickers (Year/Month → Day → Hour → Minute) entirely via callback buttons — no free-text input required.
- **`scheduler.rs`**: Two background cron jobs: (1) daily 10 PM SGT report to admin chat, (2) every-5-min cleanup to evict expired user sessions from `DashMap`.
- **`logger.rs`**: Initialises `tracing-subscriber` and exposes `AppResult<T>` / `AppError` types plus the `LogErrorExt` extension trait for ergonomic error logging.

---

## 🔄 Overall Request Flow

```
Telegram User
    │
    ▼
teloxide Dispatcher (dptree)
    ├─ /start, /new  ──────────► handlers::handle_command
    │                                  └─ build calendar keyboard (calendar.rs)
    ├─ Callback Query ─────────► handlers::handle_callback
    │                                  ├─ Calendar navigation  → rebuild keyboard
    │                                  ├─ Date selected        → llm_bazi::generate_bazi_reading
    │                                  └─ Birthtime selected   → db::save_or_update_user_bazi
    └─ Free-text Message ──────► handlers::handle_message
                                       └─ llm_bazi::generate_bazi_reading

llm_bazi::generate_bazi_reading
    ├─ almanac::fetch_and_format_almanac  (MingDecode API → filter → translate → Kong Wang)
    └─ async-openai → Dify AI endpoint   (system prompt + user bazi + almanac + history)

scheduler (background)
    ├─ 0 0 14 * * *  → tomorrow's reading → admin chat
    └─ 0 */5 * * *  → evict stale user_contexts + user_last_active
```

---

## 🧠 Architectural & Implementation Guidelines

1. **Async Contexts & Lifetimes:**
   - Always `.clone()` `Arc` bindings, SQLite pools, and `DashMap` instances before moving into `async` closures. Use `DashMap` to avoid `Mutex` deadlocks across high-traffic Telegram handlers.

2. **Database Migrations:**
   - New schema changes require a new file in `./migrations/`. Use `sqlx::query!` compile-time macros where possible.
   - Run `cargo sqlx prepare` after changing SQL queries if offline checking is enabled.

3. **Astrology Specifics (Critical):**
   - Strictly follows "Blindman Bazi" methodology (体用 Ti Yong, 做功 Zuo Gong).
   - **Do NOT** introduce generic Ziping (子平旺衰 balance theory) logic unless explicitly requested.
   - Refer to `prompt/BaziHuangLiAssistant.md` for exact AI parameters — it is embedded at compile time via `include_str!`.

4. **Timezones:**
   - The bot is configured around SGT/CST (UTC+8). Use `chrono-tz` for strict midnight roll-overs when fetching next-day almanac data.

5. **Errors & Logging:**
   - Use `tracing::info!`, `tracing::warn!`, and `tracing::error!`. Return clean error messages to users via Telegram rather than panicking.
   - Use `AppResult<T>` / `LogErrorExt` from `logger.rs` for consistent error propagation.

---

## ⚡ Quick Feature Reference

| Task                  | Where to edit                                             |
| --------------------- | --------------------------------------------------------- |
| Add a bot command     | `handlers.rs` `Command` enum + `handle_command` match arm |
| Modify shared state   | `state.rs` `AppState` struct                              |
| Add a DB table/column | New file in `./migrations/` + `db.rs`                     |
| Change API parsing    | `almanac.rs` `KEEP_SCHEMA` / `KEY_MAP`                    |
| Tweak LLM parameters  | `llm_bazi.rs` `CreateChatCompletionRequestArgs`           |
| Add a scheduled job   | `scheduler.rs` — new `Job::new_async(cron, ...)`          |
| Change configuration  | `config.rs` `AppConfig` + `.env`                          |

---

## 📄 Important Documentation Files

| File                             | Purpose                                                            |
| -------------------------------- | ------------------------------------------------------------------ |
| `README.md`                      | Top-level intro, feature list, env vars, build/run commands        |
| `prompt/BaziHuangLiAssistant.md` | System prompt — Bazi methodology constraints for LLM               |
| `DEPLOYMENT.md`                  | Raspberry Pi / DietPi ARM cross-compilation & systemd daemon setup |
| `telegramBot.service`            | Pre-configured systemd unit file for background deployment         |
| `Cargo.toml`                     | Canonical dependency list and package metadata                     |
| `.env` / `.env.example`          | Runtime secrets and configurables (never commit `.env`)            |

---

## 📁 Directory Structure

```text
DifyBaziWorkflow/
├── .env                          # App secrets (never commit)
├── .env.example                  # Template for required env vars
├── Cargo.toml                    # Cargo config and dependency tree
├── DEPLOYMENT.md                 # ARM/Raspberry Pi deployment guide
├── BaziHuangLiAssistantPrompt.md # Embedded system prompt for LLM
├── telegramBot.service           # Systemd unit file
├── src/
│   ├── main.rs                   # Entry point & bot wiring
│   ├── config.rs                 # Env config loader (AppConfig)
│   ├── state.rs                  # Shared AppState struct
│   ├── handlers.rs               # Telegram event handlers
│   ├── db.rs                     # SQLite async DB layer
│   ├── almanac.rs                # MingDecode API + Kong Wang calc
│   ├── llm_bazi.rs               # Dify/LLM prompt orchestration
│   ├── calendar.rs               # Inline keyboard calendar UI
│   ├── scheduler.rs              # Background cron jobs
│   └── logger.rs                 # Tracing init & error types
├── migrations/                   # SQLx migration SQL files
├── apiSamples/                   # Sample API response payloads
└── py_src/                       # Legacy Python implementation (archived)
```
