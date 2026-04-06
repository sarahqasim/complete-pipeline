# Complete Pipeline 

Automated extraction of **Equipment Logs** and **Submittal Logs** from PDFs using AI Automation.

## Architecture

```
app/
├── api/v1/endpoints/     # Thin route handlers (equipment, submittals)
├── schemas/              # Pydantic request/response models
├── models/               # SQLAlchemy ORM table definitions
├── db/                   # Session, engine, Base
├── services/
│   ├── shared/           # Extraction logic reused by both pipelines
│   │   ├── spec/         # Spec PDF parsing + entity extraction
│   │   ├── drawing/      # Drawing PDF schedule + vision extraction
│   │   └── retrieval/    # Fuzzy entity matching
│   ├── equipment/        # Equipment-specific: candidates → resolve → output
│   └── submittal/        # Submittal-specific: candidates → resolve → output
├── middleware/            # Request logging
├── utils/                # File + text helpers
└── config.py             # All env-var settings
```

## Quick Start

1. Copy `.env.example` to `.env` and fill in your API keys.
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `uvicorn app.main:app --reload`
4. Open: `http://localhost:8000/docs`

## API Flow

**Equipment Log:**
```
POST /api/v1/equipment/upload
POST /api/v1/equipment/{job_id}/process
GET  /api/v1/equipment/{job_id}/result
GET  /api/v1/equipment/{job_id}/download
```

**Submittal Log:**
```
POST /api/v1/submittals/upload
POST /api/v1/submittals/{job_id}/process
GET  /api/v1/submittals/{job_id}/result
GET  /api/v1/submittals/{job_id}/download
POST /api/v1/submittals/{job_id}/validate
```

## Requirements

- Python 3.11+
- Poppler (for submittal drawing vision): set `POPPLER_PATH` in `.env`
- API Keys: Anthropic (equipment drawings), Gemini (submittal drawings + synthesis)
