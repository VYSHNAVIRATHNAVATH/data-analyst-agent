# AnalystGPT — Autonomous Business Intelligence Agent

An autonomous AI agent that answers plain-English questions about your data — reasoning step by step, writing and executing pandas code, generating charts, forecasting trends, and delivering executive-style insight reports automatically.

## 🔗 Live Demo
[Click here to try it live →](https://data-analyst-agent-g2lnfhkyjrggbg5ekjekfn.streamlit.app/)

## 🤖 What it does

Ask a question like:
> "Which product category had the highest revenue in 2024? Visualize it."

The agent will:
1. Load and inspect your CSV automatically
2. Write and execute pandas code to analyze the data
3. Generate a professional matplotlib chart
4. Forecast future trends using Prophet
5. Write an executive insight report
6. Export everything as a downloadable PDF

## 🏗️ Architecture

```
User Question
     ↓
ReAct Agent (LLaMA 3.3 70B via Groq)
     ↓
Tool 1: load_csv()        — inspects schema
Tool 2: execute_code()    — runs pandas analysis
Tool 3: generate_chart()  — creates matplotlib PNG
Tool 4: forecast()        — Prophet time-series forecast
     ↓
Narrator LLM              — writes insight report
     ↓
PDF Generator             — creates downloadable report
     ↓
Streamlit Dashboard       — displays everything live
```

## ✨ Key Features

- **ReAct reasoning** — Thought → Action → Observation loop with live trace
- **Autonomous code generation** — writes and executes pandas code dynamically
- **Self-correcting** — retries on tool errors automatically
- **Conversational memory** — supports follow-up questions
- **4 agent tools** — CSV loader, code executor, chart generator, Prophet forecaster
- **Chart generation** — bar, line, pie charts saved as PNG
- **Time-series forecasting** — predict next 3 months with confidence intervals
- **Insight narration** — executive report with Summary, Numbers, Insight, Recommendation
- **PDF export** — download full report with embedded chart
- **CSV upload** — works with any dataset

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | LLaMA 3.3 70B via Groq API |
| Agent pattern | ReAct (Reasoning + Acting) |
| Tool calling | Groq function calling |
| Data analysis | pandas |
| Visualization | matplotlib |
| Forecasting | Facebook Prophet |
| PDF generation | ReportLab |
| UI | Streamlit |
| Language | Python 3.10+ |

## 🚀 Setup

```bash
git clone https://github.com/VYSHNAVIRATHNAVATH/data-analyst-agent
cd data-analyst-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:
```
GROQ_API_KEY=your_key_here
```

Run:
```bash
streamlit run app.py
```

## 💡 Example Questions

- Which product category had the highest total revenue in 2024?
- Who is the top performing sales rep by revenue?
- Show monthly revenue trend for 2023 vs 2024
- Predict revenue for the next 3 months
- Which region has the highest units sold?
- What are the top 5 products by revenue?
- Compare Electronics vs Furniture revenue by region

## 📁 Project Structure

```
data-analyst-agent/
├── data/
│   └── sales_data.csv        # 1033-row realistic sales dataset
├── tools/
│   ├── csv_loader.py         # Tool 1: loads CSV into memory
│   ├── code_executor.py      # Tool 2: executes pandas code safely
│   ├── chart_generator.py    # Tool 3: generates matplotlib charts
│   ├── forecaster.py         # Tool 4: Prophet forecasting
│   └── tool_schemas.py       # Tool definitions for LLM
├── utils/
│   ├── llm_client.py         # Groq API wrapper with retry logic
│   ├── narrator.py           # Insight report generator
│   └── pdf_generator.py      # PDF report generator
├── app.py                    # Streamlit UI
├── main.py                   # CLI agent runner
└── requirements.txt
```

## 📊 Dataset

1033 rows · 2 years (2023–2024) · 20 products · 3 categories · 5 regions · 10 sales reps · ₹4.2 crore total revenue · Seasonal patterns built in

---

Built with ❤️ using LLaMA 3.3 70B · Groq · ReAct · pandas · Prophet · Streamlit