# FastAPI Main Application - Quick Start (5 minutes)

## Step 1: Install Dependencies (1 minute)

```bash
cd /home/ubuntu/Desktop/demo
pip install -r requirements.txt
```

## Step 2: Configure Environment (30 seconds)

```bash
# Copy example configuration
cp .env.example .env

# Edit .env and add your Anthropic API key
# (or keep defaults for testing)
```

## Step 3: Start the Application (30 seconds)

```bash
python main.py
```

You should see:
```
INFO:     Application startup complete
```

## Step 4: Verify It's Running (30 seconds)

Open in your browser or curl:

```bash
# Quick health check
curl http://localhost:8000/health

# Access interactive docs
# Open: http://localhost:8000/docs
```

---

## 5-Minute Tutorial

### 1. Check Health (10 seconds)

```bash
curl http://localhost:8000/health
```

### 2. Submit an Application (30 seconds)

```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "personal_info": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "+14155552671",
      "date_of_birth": "1990-05-15"
    },
    "employment_info": {
      "employer_name": "Tech Corp",
      "job_title": "Engineer",
      "employment_status": "employed",
      "years_employed": 5.0,
      "monthly_income": 8000
    },
    "financial_info": {
      "annual_income": 96000,
      "monthly_expenses": 3000,
      "credit_score": 750,
      "existing_loans_count": 1,
      "savings_amount": 50000
    },
    "loan_details": {
      "loan_amount": 250000,
      "loan_term_months": 360,
      "loan_purpose": "home",
      "collateral_type": "property",
      "collateral_value": 300000
    }
  }'
```

Copy the `application_id` from the response.

### 3. Check Application Status (20 seconds)

```bash
curl http://localhost:8000/api/v1/applications/APP-20240619-000001
```

Replace the app ID with the one you got above.

### 4. Query Decisions (30 seconds)

```bash
# Get first 10 decisions
curl http://localhost:8000/api/v1/decisions

# Get approved decisions only
curl "http://localhost:8000/api/v1/decisions?decision_filter=approved"

# Filter by risk score
curl "http://localhost:8000/api/v1/decisions?min_risk_score=30&max_risk_score=70"

# Sort and paginate
curl "http://localhost:8000/api/v1/decisions?page=1&page_size=5&sort_by=risk_score&sort_order=desc"
```

### 5. Use Interactive Docs (2 minutes)

Open http://localhost:8000/docs and:
- Try each endpoint
- See request/response models
- Explore parameters

---

## Common Commands

```bash
# Start API
python main.py

# Run tests
pytest test_fastapi_main.py -v

# Run example client
python fastapi_client_example.py

# With Docker
docker build -f Dockerfile.fastapi -t loan-api .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_key loan-api

# With Docker Compose
docker-compose -f docker-compose.fastapi.yml up -d
docker-compose -f docker-compose.fastapi.yml logs -f
```

---

## Validation Rules

When submitting applications, remember:

- **Email**: Must be valid email format
- **Phone**: +1 followed by digits (e.g., +14155552671)
- **Date**: YYYY-MM-DD format
- **Credit Score**: 300-850
- **Loan Amount**: Up to $1,000,000
- **Debt-to-Income Ratio**: Maximum 50% allowed
- **Employment Status**: employed, self-employed, unemployed, or retired

---

## Example Application IDs

The API auto-generates IDs like:
```
APP-20240619-000001
APP-20240619-000002
```

Format: `APP-YYYYMMDD-XXXXXX`

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | System status |
| `/api/v1/applications` | POST | Submit application |
| `/api/v1/applications/{app_id}` | GET | Check status |
| `/api/v1/decisions` | GET | Query decisions |
| `/docs` | GET | Interactive documentation |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | Change `API_PORT` in `.env` |
| Module not found | Run `pip install -r requirements.txt` again |
| API won't start | Check `.env` file exists and has required vars |
| CORS errors | Verify `FRONTEND_URL` environment variable |

---

## Next Steps

1. **Read full documentation:** `FASTAPI_MAIN_GUIDE.md`
2. **Run tests:** `pytest test_fastapi_main.py`
3. **Try examples:** `python fastapi_client_example.py`
4. **Deploy:** Use Docker or Docker Compose
5. **Customize:** Update `.env` and configuration

---

## Files Created

- `main.py` - Main FastAPI application
- `requirements.txt` - Python dependencies
- `.env.example` - Environment template
- `Dockerfile.fastapi` - Docker configuration
- `docker-compose.fastapi.yml` - Multi-service setup
- `FASTAPI_MAIN_GUIDE.md` - Complete documentation
- `FASTAPI_README.md` - Detailed README
- `FASTAPI_QUICKSTART.md` - This file
- `fastapi_client_example.py` - Example client code
- `test_fastapi_main.py` - Unit tests

---

## Success Indicators

You'll know everything is working when:

✓ `python main.py` runs without errors
✓ http://localhost:8000/health returns status
✓ http://localhost:8000/docs loads in browser
✓ POST to `/api/v1/applications` returns app ID
✓ GET to `/api/v1/applications/{app_id}` returns status

---

## What's Included

### Core API Features
- ✓ Health monitoring endpoint
- ✓ Loan application submission with Pydantic validation
- ✓ Application status checking
- ✓ Decision querying with filtering and pagination
- ✓ Error handling middleware
- ✓ CORS setup
- ✓ Startup/shutdown event handling
- ✓ LangGraph orchestrator initialization

### Production Ready
- ✓ Comprehensive validation
- ✓ Proper error responses
- ✓ Logging and monitoring
- ✓ Docker configuration
- ✓ Unit tests
- ✓ Documentation

---

**That's it! You now have a fully functional Loan Decision API. 🚀**
