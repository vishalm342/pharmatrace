# 🔬 PharmaTrace

> **If you can't observe your AI agents, you don't own them.**

PharmaTrace is an AI-powered drug interaction checker agent — fully instrumented with OpenTelemetry and observable via SigNoz. Every LLM call, every tool invocation, every FDA API request is traced, logged, and metered in real time.

Built for the [Agents of SigNoz Hackathon 2026](https://www.wemakedevs.org/hackathons/signoz).

---

## 🧠 The Problem

Health-tech developers use LLM-powered agents to check drug interactions. When these agents fail — wrong answer, timeout, hallucination — **nobody can debug why**. Was it a bad prompt? A slow FDA API call? A model error? In healthcare, that’s not acceptable.

PharmaTrace makes every step of the agent’s reasoning chain **fully visible and debuggable**.

---

## ⚙️ Full Tech Stack

### 🔧 Backend
| Tool | Purpose |
|---|---|
| `Python 3.11+` | Core language |
| `FastAPI` | REST API server |
| `Uvicorn` | ASGI server |
| `python-dotenv` | Env variable management |
| `httpx` | Async HTTP client for OpenFDA calls |

### 🤖 AI / LLM Layer
| Tool | Purpose |
|---|---|
| `LangChain` | Agent framework — tool calling + orchestration |
| `langchain-groq` | Groq LLM integration |
| `Groq API` | Free LLM inference (llama-3.3-70b) |
| `OpenFDA API` | Real drug interaction data (no auth needed) |

### 📡 Observability
| Tool | Purpose |
|---|---|
| `opentelemetry-sdk` | Core OTel tracing + metrics |
| `opentelemetry-api` | OTel API layer |
| `opentelemetry-exporter-otlp-proto-http` | Exports to SigNoz |
| `opentelemetry-instrumentation-fastapi` | Auto-instruments FastAPI routes |
| `opentelemetry-instrumentation-httpx` | Auto-instruments outbound HTTP |
| `traceloop-sdk` | Auto-instruments LangChain LLM calls |
| `SigNoz Cloud` | Traces, logs, metrics, dashboards, alerts |

### 🎨 Frontend
| Tool | Purpose |
|---|---|
| `Streamlit` | Interactive UI for drug interaction queries |

### 🚀 Infra
| Tool | Purpose |
|---|---|
| `Docker + docker-compose` | Containerization |
| `Render (free tier)` | Live deployment |

---

## 🏗️ Architecture

```
[Streamlit UI]
      │
      ▼
[FastAPI Backend] ──────────────────────────────────┐
      │                                              │
      ▼                                      [OTel Exporter]
[LangChain Agent]                                    │
   ├── Tool: OpenFDA Drug Lookup                     ▼
   ├── Tool: Drug Interaction Check          [SigNoz Cloud]
   └── LLM: Groq llama-3.3-70b            Traces | Logs |
                                         Metrics | Alerts
```

---

## 📁 Project Structure

```
pharmatrace/
├── backend/
│   ├── main.py              # FastAPI app + routes
│   ├── agent.py             # LangChain agent
│   ├── tools.py             # OpenFDA tool functions
│   └── telemetry.py         # OTel setup + SigNoz config
├── frontend/
│   └── app.py               # Streamlit UI
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🔑 Environment Variables

```env
GROQ_API_KEY=your_groq_api_key
SIGNOZ_ENDPOINT=https://ingest.us.signoz.cloud:443
SIGNOZ_ACCESS_TOKEN=your_signoz_token
TRACELOOP_BASE_URL=https://ingest.us.signoz.cloud:443
```

---

## 🚀 Quickstart

```bash
git clone https://github.com/vishalm342/pharmatrace
cd pharmatrace
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
uvicorn backend.main:app --reload
# In another terminal:
streamlit run frontend/app.py
```

---

## 📊 What You See in SigNoz

- **Trace waterfall** — HTTP request → agent → LLM call → FDA API → response
- **Custom metrics** — token usage per query, latency, FDA API duration
- **Logs** — every prompt + response captured
- **Dashboard** — Avg latency, tokens/query, error rate, queries/hour
- **Alert** — fires when token usage > 500 per request

---

## 👨‍💻 Built By

**Vishal M** — [Portfolio](https://vishalm-portfolio.netlify.app/) | [GitHub](https://github.com/vishalm342)

*Agents of SigNoz Hackathon 2026 — Track 01: AI & Agent Observability*
