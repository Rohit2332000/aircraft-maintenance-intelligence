# ✈️ Aircraft Maintenance Intelligence

> AI-powered aircraft maintenance decision-support system combining historical flight-data analytics, statistical anomaly detection, maintenance-manual knowledge retrieval, LangGraph orchestration, and LLM-based maintenance recommendations.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-Build-646CFF?logo=vite&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange)
![LangChain](https://img.shields.io/badge/LangChain-RAG-green)
![Groq](https://img.shields.io/badge/Groq-LLM-black)
![Pandas](https://img.shields.io/badge/Pandas-Analytics-150458?logo=pandas&logoColor=white)

---

## 🚀 Overview

**Aircraft Maintenance Intelligence** is an end-to-end AI-assisted maintenance analysis platform that converts aircraft flight data into explainable and actionable maintenance intelligence.

Instead of displaying only raw sensor values, the system combines:

- Historical statistical analysis
- Z-score based anomaly detection
- Parameter trend analysis
- Maintenance-manual thresholds
- Failure-mode knowledge
- Troubleshooting and inspection guidance
- Maintenance recommendations
- LangGraph workflow orchestration
- Groq LLM reasoning
- FastAPI backend APIs
- React + Vite dashboard visualization
- LangSmith observability

The core objective is:

> **Given the current aircraft condition, identify what is abnormal, understand why it is abnormal, retrieve the relevant maintenance knowledge, and produce an explainable maintenance recommendation.**

---

## 🎯 Problem

Aircraft continuously generate operational measurements such as:

- Engine Temperature
- Exhaust Gas Temperature
- Oil Temperature
- Oil Pressure
- Engine Vibration
- Compressor Pressure
- Fuel Flow
- Hydraulic Pressure
- Engine RPM
- Ambient Temperature
- Humidity
- Outside Air Temperature

A raw value alone is not enough for a useful maintenance decision.

For example:

```text
Engine Vibration = 5.9 mm/s
```

The system turns that into:

```text
Current Value       : 5.9 mm/s
Historical Mean     : 3.49 mm/s
Z-Score             : 1.69
Trend               : Increasing
Manual Status       : Critical
Priority            : Critical
Failure Mode        : Bearing Wear

Recommended Action:
Inspect bearing assembly and rotating components.
```

---

# 💡 Solution

The system combines three sources of intelligence:

```text
Flight Data
    +
Historical Analytics
    +
Maintenance Knowledge
    +
LangGraph Orchestration
    +
LLM Reasoning
    =
Maintenance Intelligence
```

End-to-end flow:

```text
Aircraft Flight Data
        │
        ▼
Data Validation
        │
        ▼
Historical Analytics
        │
        ├── Mean
        ├── Median
        ├── Standard Deviation
        ├── Z-Score
        ├── Percentage Change
        └── Trend
        │
        ▼
Statistical Anomaly Detection
        │
        ▼
Maintenance Manual Classification
        │
        ├── Normal
        ├── Warning
        └── Critical
        │
        ▼
Knowledge Retrieval
        │
        ├── Failure Modes
        ├── Symptoms
        ├── Causes
        ├── Troubleshooting
        ├── Inspection
        └── Maintenance Actions
        │
        ▼
LangGraph Workflow
        │
        ▼
Groq LLM
        │
        ▼
Structured Maintenance Result
        │
        ▼
FastAPI
        │
        ▼
React Dashboard
```

---

# 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                    MAINTENANCE ENGINEER                      │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Excel + Aircraft ID
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                     REACT + VITE FRONTEND                    │
│                                                              │
│  Aircraft Overview  │  Parameter Monitoring                  │
│  Risk Dashboard     │  Anomaly Analysis                      │
│  Recommendations    │  Maintenance Evidence                  │
└────────────────────────────┬─────────────────────────────────┘
                             │ REST API
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                         FASTAPI                              │
│                         app.py                               │
│                                                              │
│ Upload → Validate → Normalize → Pipeline → JSON             │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                       pipeline.py                            │
│                                                              │
│                Complete Analysis Pipeline                    │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                        graph.py                              │
│                       LANGGRAPH                              │
│                                                              │
│ START → Analytics → Classification → Retrieval →             │
│ Evidence → LLM Reasoning → Structured Result → END           │
└─────────────┬──────────────────┬─────────────────────────────┘
              │                  │
              ▼                  ▼
     ┌────────────────┐   ┌────────────────────┐
     │   Analytics    │   │     Retriever      │
     │ analytics.py   │   │   retriever.py     │
     │                │   │                    │
     │ Mean           │   │ Manual evidence    │
     │ Median         │   │ Failure modes     │
     │ Std            │   │ Procedures        │
     │ Z-score        │   │ Maintenance       │
     │ Trend          │   │ Context            │
     │ Anomaly        │   │                    │
     └───────┬────────┘   └─────────┬──────────┘
             │                      │
             └──────────┬───────────┘
                        ▼
                 ┌───────────────┐
                 │  classifier   │
                 │               │
                 │ Normal        │
                 │ Warning       │
                 │ Critical      │
                 │ Unknown       │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │    llm.py     │
                 │               │
                 │   Groq LLM    │
                 │   Reasoning   │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ Structured    │
                 │ JSON Result   │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ React UI      │
                 └───────────────┘
```

---

# 🔄 End-to-End Workflow

## 1. Upload Aircraft Data

The user uploads an Excel workbook and selects an aircraft.

Example:

```text
Aircraft ID: AIR-002
File: aircraft_maintenance_intelligence_dataset.xlsx
```

## 2. FastAPI Validation

The API validates:

- Aircraft ID
- File extension
- Empty files
- Required columns
- Numeric flight-cycle values
- Aircraft existence

## 3. Data Normalization

Uploaded Excel columns are normalized to consistent backend parameter names.

## 4. Historical Analytics

For each supported parameter, the system calculates:

- Current value
- Historical mean
- Median
- Standard deviation
- Difference from mean
- Percentage change
- Z-score
- Trend

Z-score:

```text
z = (x - μ) / σ
```

where:

```text
x = current value
μ = historical mean
σ = historical standard deviation
```

## 5. Statistical Anomaly Detection

The system identifies values that behave differently from historical observations.

Example:

```text
Engine Vibration

Current       : 5.9 mm/s
Mean          : 3.49 mm/s
Std           : 1.43
Z-Score       : 1.69
Trend         : Increasing
Status        : Anomaly
```

## 6. Maintenance Manual Classification

Current readings are compared with domain-specific thresholds:

```text
NORMAL
WARNING
CRITICAL
UNKNOWN
```

Example:

```text
Engine Vibration

Normal:
0 – 3.1 mm/s

Warning:
3.1 – 4.7 mm/s

Critical:
> 4.7 mm/s

Current:
5.9 mm/s

Manual Status:
CRITICAL
```

## 7. Knowledge Retrieval

For abnormal parameters, the retriever finds relevant maintenance knowledge, including:

- Normal ranges
- Warning thresholds
- Critical thresholds
- Failure modes
- Symptoms
- Causes
- Troubleshooting
- Inspection procedures
- Maintenance actions
- Detection logic
- Manual references

## 8. LangGraph Orchestration

LangGraph coordinates the workflow:

```text
START
  ↓
Input Validation
  ↓
Analytics
  ↓
Anomaly Detection
  ↓
Classification
  ↓
Knowledge Retrieval
  ↓
Evidence Construction
  ↓
LLM Reasoning
  ↓
Structured Output
  ↓
END
```

This makes the system modular, traceable, testable, and easier to extend.

## 9. LLM Reasoning

The Groq LLM receives:

```text
Current Parameter
+
Historical Statistics
+
Anomaly Status
+
Trend
+
Manual Status
+
Retrieved Evidence
+
Failure Modes
+
Maintenance Instructions
```

It generates structured maintenance reasoning.

---

# 🛡️ Grounded AI Design

The project is intentionally designed to avoid:

```text
Raw Data → LLM → Guess
```

Instead:

```text
Raw Data
   ↓
Historical Analytics
   ↓
Statistical Evidence
   +
Maintenance Knowledge
   ↓
Retrieval
   ↓
LangGraph
   ↓
LLM Reasoning
   ↓
Explainable Recommendation
```

The LLM is primarily used for **reasoning, synthesis, and explanation**, while deterministic analytics and domain knowledge establish the evidence.

---

# 🖥️ Frontend Dashboard

The React dashboard is designed around a maintenance engineer's workflow.

## Aircraft Overview

```text
AIR-002

Risk Score
77.2%

Remaining Useful Life
30 cycles

Parameters Analyzed
14

Anomalies
9

Maintenance Required
9

Status
MAINTENANCE DUE
```

## Parameter Monitoring

Each parameter can display:

```text
Parameter
Current Value
Unit
Historical Mean
Median
Standard Deviation
Z-Score
Trend
Manual Status
Statistical Status
Priority
Maintenance Required
```

## Critical Parameters

The dashboard prioritizes parameters requiring immediate attention.

Example:

| Parameter               |      Current | Status   | Priority | Recommended Action                             |
| ----------------------- | -----------: | -------- | -------- | ---------------------------------------------- |
| Engine Temperature      |    714.3 °C | Critical | Critical | Inspect cooling air ducts and combustion liner |
| Exhaust Gas Temperature |    685.7 °C | Critical | Critical | Inspect turbine section                        |
| Oil Temperature         |     99.7 °C | Critical | Critical | Inspect oil cooler and scavenge lines          |
| Oil Pressure            |       49 PSI | Critical | Critical | Inspect oil pump, filter and seals             |
| Engine Vibration        |     5.9 mm/s | Critical | Critical | Inspect bearing assembly                       |
| Compressor Pressure     |     44.5 PSI | Critical | Critical | Inspect variable stator vane schedule          |
| Fuel Flow               | 2449.4 kg/hr | Critical | Critical | Check fuel metering unit calibration           |

## Maintenance Evidence

For each recommendation, the frontend can show:

- Manual status
- Failure mode
- Relevant evidence
- Recommended action
- Reasoning
- Confidence
- Source/reference information

---

# 📦 API Output

The backend returns structured JSON.

Example:

```json
{
  "aircraft": {
    "aircraft_id": "AIR-002",
    "risk_score": 77.2,
    "remaining_useful_life": 30,
    "overall_status": "Maintenance Due",
    "parameters_analyzed": 14,
    "anomalies_detected": 9,
    "maintenance_required_count": 9
  },
  "parameters": [
    {
      "parameter": "Engine_Vibration_(mm/s)",
      "display_name": "Engine Vibration",
      "unit": "mm/s",
      "analytics": {
        "latest_value": 5.9,
        "historical": {
          "count": 99,
          "mean": 3.485,
          "median": 3.51,
          "std": 1.43,
          "minimum": 0.94,
          "maximum": 5.97
        },
        "difference_from_mean": 2.414,
        "percentage_change": 69.27,
        "z_score": 1.69,
        "trend": "INCREASING",
        "statistical_anomaly": true,
        "statistical_status": "ANOMALY"
      },
      "normal_range": [0, 3.1],
      "manual_status": "Critical",
      "manual_evidence_available": true,
      "maintenance": {
        "maintenance_required": true,
        "priority": "CRITICAL",
        "recommended_action": "Inspect bearing assembly and rotating components",
        "reasoning": "Current vibration exceeds the critical threshold.",
        "failure_modes": [
          {
            "failure_mode_id": "5.1.1",
            "name": "Bearing Wear"
          }
        ],
        "confidence": "HIGH"
      }
    }
  ],
  "pipeline_version": "1.1.0"
}
```

---

# 🌐 API Endpoints

## Root

```http
GET /
```

## Health

```http
GET /health
```

## Aircraft Analysis

```http
POST /api/v1/aircraft/{aircraft_id}/analysis
```

### Multipart Request

```text
aircraft_id = AIR-002
file = aircraft_maintenance_intelligence_dataset.xlsx
```

### cURL

```bash
curl -X POST   "http://localhost:8000/api/v1/aircraft/AIR-002/analysis"   -F "file=@aircraft_maintenance_intelligence_dataset.xlsx"
```

---

# 📁 Project Structure

```text
aircraft-maintenance-intelligence/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .gitignore
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   ├── classifier.py
│   │   ├── config.py
│   │   ├── data_loader.py
│   │   ├── graph.py
│   │   ├── kb_data.py
│   │   ├── llm.py
│   │   ├── pipeline.py
│   │   ├── prompts.py
│   │   ├── retriever.py
│   │   └── schemas.py
│   │
│   ├── test.py
│   ├── test_analytics.py
│   └── test_retriever.py
│
├── aircraft-maintenance-frontend1/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── .env.example
│   ├── .gitignore
│   │
│   └── src/
│       ├── App.jsx
│       ├── index.css
│       └── main.jsx
│
└── README.md
```

---

# 🧩 Backend Modules

| File               | Responsibility                                   |
| ------------------ | ------------------------------------------------ |
| `app.py`         | FastAPI application, uploads, validation and API |
| `pipeline.py`    | High-level analysis pipeline                     |
| `graph.py`       | LangGraph workflow orchestration                 |
| `analytics.py`   | Historical statistics and anomaly detection      |
| `classifier.py`  | Normal/Warning/Critical classification           |
| `retriever.py`   | Maintenance knowledge retrieval                  |
| `kb_data.py`     | Structured maintenance knowledge                 |
| `llm.py`         | Groq LLM integration                             |
| `prompts.py`     | LLM prompts                                      |
| `schemas.py`     | Structured data schemas                          |
| `data_loader.py` | Dataset loading and preprocessing                |
| `config.py`      | Application configuration                        |

---

# 🧪 Testing

The backend contains tests for core functionality:

```text
test.py
test_analytics.py
test_retriever.py
```

Run:

```bash
python test.py
```

```bash
python test_analytics.py
```

```bash
python test_retriever.py
```

Or, if configured with pytest:

```bash
pytest
```

---

# ⚙️ Environment Variables

Create:

```text
backend/.env
```

Example:

```env
GROQ_API_KEY=your_groq_api_key
MODEL_NAME=your_model_name

LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=aircraft-maintenance-intelligence
```

Never commit real secrets.

Commit only:

```text
.env.example
```

---

# 🛠️ Backend Setup

```bash
cd backend
```

Create virtual environment:

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scriptsctivate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn app:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

---

# 🎨 Frontend Setup

```bash
cd aircraft-maintenance-frontend1
```

Install:

```bash
npm install
```

Run:

```bash
npm run dev
```

---

# 🔗 Frontend ↔ Backend

The frontend sends:

```text
Excel File
+
Aircraft ID
```

to:

```http
POST /api/v1/aircraft/{aircraft_id}/analysis
```

The backend returns:

```text
JSON
```

React transforms that JSON into:

```text
Aircraft Overview
+
Risk Cards
+
Critical Alerts
+
Parameter Cards
+
Anomaly Information
+
Maintenance Recommendations
+
Failure Modes
+
Manual Evidence
```

---

# 🔬 LangSmith

LangSmith can be used to observe and debug the LangGraph workflow.

Conceptually:

```text
User Request
     ↓
LangGraph
     ↓
Analytics Node
     ↓
Retriever Node
     ↓
Evidence Node
     ↓
LLM Node
     ↓
Final Result
```

This helps inspect:

- Node execution
- Retrieval behavior
- LLM calls
- Latency
- Errors
- Token usage
- Workflow failures
- End-to-end traces

---

# 🔐 Security

Do not commit:

```text
.env
venv/
__pycache__/
*.pyc
node_modules/
dist/
build/
outputs/
API keys
Private datasets
Secrets
```

Use:

```text
.env.example
```

to document required configuration without exposing secrets.

---

# 🚀 Deployment

The project can be deployed as two services:

```text
                 INTERNET
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   React Frontend        FastAPI Backend
          │                   │
          │                   ▼
          │              LangGraph
          │                   │
          │          ┌────────┴────────┐
          │          │                 │
          │      Retriever           Groq
          │          │                 │
          └──────────┴─────────────────┘
                         │
                         ▼
                  Maintenance UI
```

The frontend and backend can be deployed independently and connected through the FastAPI URL.

---

# 📈 Future Improvements

## Real-Time Sensor Streaming

Replace Excel uploads with live telemetry.

```text
Aircraft Sensors
      ↓
Streaming
      ↓
Analytics
      ↓
Real-Time Alerts
```

## Predictive Maintenance

Move from:

```text
What is abnormal now?
```

to:

```text
What is likely to fail next?
```

## RUL Prediction

Build a dedicated Remaining Useful Life model.

Potential approaches:

- LSTM
- Temporal Transformers
- Time-series forecasting
- Survival analysis

## Historical Trend Visualization

Display parameter behavior across flight cycles.

## Real-Time Alerts

Notify engineers when critical conditions are detected.

## Database Integration

Persist:

- Aircraft
- Flights
- Parameters
- Alerts
- Maintenance events
- Recommendations
- Audit history

## Production Observability

Track:

- Latency
- Retrieval quality
- LLM failures
- Token usage
- Workflow failures
- Recommendation quality

---

# ⚠️ Disclaimer

This project is a **training, research, and engineering demonstration system**.

It must not be used as the sole basis for real-world aircraft maintenance decisions.

Actual aircraft maintenance must follow approved documentation, manufacturer procedures, regulatory requirements, certified engineering processes, qualified personnel, and applicable safety standards.

AI-generated recommendations should be independently verified before operational use.

---

# 🎓 What This Project Demonstrates

### Data Engineering

- Excel ingestion
- Data cleaning
- Column normalization
- Validation
- Pandas processing

### Statistics / ML

- Historical analysis
- Z-score analysis
- Anomaly detection
- Trend analysis
- Statistical comparison

### Generative AI

- LLM integration
- Structured prompting
- Context-aware reasoning
- Grounded recommendations

### RAG

- Maintenance knowledge retrieval
- Evidence selection
- Context construction
- Domain grounding

### Agentic AI

- LangGraph orchestration
- Stateful workflows
- Modular graph nodes
- Retrieval/tool execution

### Backend Engineering

- FastAPI
- REST APIs
- File uploads
- Validation
- Error handling
- Structured JSON

### Frontend Engineering

- React
- Vite
- Dashboard design
- API integration
- Data visualization

### AI Observability

- LangSmith
- LangGraph tracing
- Debugging
- LLM monitoring

---

# ⭐ Why This Project Matters

This project goes beyond a basic chatbot or simple RAG demo.

It demonstrates an end-to-end AI engineering workflow:

```text
Aircraft Data
      ↓
Data Validation
      ↓
Statistical Analytics
      ↓
Anomaly Detection
      ↓
Domain Classification
      ↓
Knowledge Retrieval
      ↓
LangGraph
      ↓
LLM Reasoning
      ↓
Structured Maintenance Decision
      ↓
FastAPI
      ↓
React Dashboard
      ↓
Maintenance Engineer
```

The result is an **explainable AI-assisted maintenance system** where analytics provides the signal, domain knowledge provides the evidence, LangGraph coordinates the workflow, and the LLM converts the evidence into a readable recommendation.

---

# 👨‍💻 Author

**Rohit Kumar Yadav**

AI / ML Engineer

Focus areas:

```text
Python
GenAI
RAG
LangGraph
LangChain
FastAPI
Machine Learning
LLMs
React
AI Systems
```

GitHub:

https://github.com/Rohit2332000

Repository:

https://github.com/Rohit2332000/aircraft-maintenance-intelligence

---

# 📄 License

This project is available under the MIT License.

---

# ✨ Final Summary

```text
┌──────────────────────────────────────────────────────┐
│          AIRCRAFT MAINTENANCE INTELLIGENCE           │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Aircraft Flight Data                                │
│          ↓                                           │
│  Historical Analytics                                │
│          ↓                                           │
│  Anomaly Detection                                   │
│          ↓                                           │
│  Maintenance Knowledge                               │
│          ↓                                           │
│  Retrieval                                           │
│          ↓                                           │
│  LangGraph                                           │
│          ↓                                           │
│  Groq LLM                                            │
│          ↓                                           │
│  Explainable Recommendation                          │
│          ↓                                           │
│  FastAPI                                              │
│          ↓                                           │
│  React Dashboard                                      │
│          ↓                                           │
│  Maintenance Intelligence                            │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Built to demonstrate how analytics, retrieval, agentic orchestration, LLM reasoning, backend APIs, observability, and frontend engineering can work together in one practical AI system.**
