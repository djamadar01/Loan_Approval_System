# FastAPI Main Application - README

## Quick Start

### Prerequisites

- Python 3.9+
- pip or poetry
- Optional: Docker and Docker Compose

### Installation

1. **Clone and setup:**
   ```bash
   cd /home/ubuntu/Desktop/demo
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set your ANTHROPIC_API_KEY
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

   The API will start at `http://localhost:8000`

### Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# View API documentation
# Open in browser: http://localhost:8000/docs
```

---

## Project Structure

```
/home/ubuntu/Desktop/demo/
├── main.py                      # Main FastAPI application
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .env                         # Actual environment variables (create from .env.example)
├── Dockerfile.fastapi           # Docker configuration
├── docker-compose.fastapi.yml   # Docker Compose for multi-service setup
├── FASTAPI_MAIN_GUIDE.md        # Complete API documentation
├── FASTAPI_README.md            # This file
├── fastapi_client_example.py    # Example client code
├── test_fastapi_main.py         # Unit tests
└── loan_orchestrator.py         # LangGraph orchestrator (optional)
```

---

## Core Features

### 1. Health Monitoring (`/health`)

Real-time system status including orchestrator and database connectivity.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-19T10:30:00.000000",
  "version": "1.0.0",
  "orchestrator_ready": true,
  "database_connected": true
}
```

### 2. Loan Application Submission (`POST /api/v1/applications`)

Submit a new loan application with comprehensive validation.

```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "personal_info": {...},
    "employment_info": {...},
    "financial_info": {...},
    "loan_details": {...}
  }'
```

**Validation includes:**
- Email format validation
- Phone number validation
- Date format validation (YYYY-MM-DD)
- Credit score range (300-850)
- Debt-to-income ratio (max 50%)

### 3. Application Status Retrieval (`GET /api/v1/applications/{app_id}`)

Check the processing status of a submitted application.

```bash
curl http://localhost:8000/api/v1/applications/APP-20240619-000001
```

### 4. Decision Management (`GET /api/v1/decisions`)

Query decisions with advanced filtering and pagination.

```bash
# Get first page
curl http://localhost:8000/api/v1/decisions

# Filter by decision type
curl "http://localhost:8000/api/v1/decisions?decision_filter=approved"

# Filter by risk score
curl "http://localhost:8000/api/v1/decisions?min_risk_score=30&max_risk_score=70"

# Sort and paginate
curl "http://localhost:8000/api/v1/decisions?page=2&page_size=20&sort_by=risk_score&sort_order=asc"
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/` | API root information |
| GET | `/api/v1` | API v1 information |
| POST | `/api/v1/applications` | Submit new application |
| GET | `/api/v1/applications/{app_id}` | Get application status |
| GET | `/api/v1/decisions` | Query decisions |

### Documentation Endpoints

| Endpoint | Description |
|----------|-------------|
| `/docs` | Swagger UI (interactive) |
| `/redoc` | ReDoc (static) |
| `/openapi.json` | OpenAPI schema |

---

## Configuration

### Environment Variables

```env
# API Server
API_HOST=0.0.0.0          # Server host
API_PORT=8000             # Server port
DEBUG=false               # Debug mode

# Frontend
FRONTEND_URL=http://localhost:3000

# Anthropic
ANTHROPIC_API_KEY=your_key_here

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/db

# Logging
LOG_LEVEL=INFO
```

### Update Configuration

Edit `.env` file and restart the application:

```bash
# Edit .env
nano .env

# Restart application
python main.py
```

---

## Running the Application

### Development Mode

```bash
# With auto-reload
DEBUG=true python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# With uvicorn workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with Gunicorn
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Docker

```bash
# Build image
docker build -f Dockerfile.fastapi -t loan-decision-api .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  loan-decision-api

# With environment file
docker run -p 8000:8000 --env-file .env loan-decision-api
```

### Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.fastapi.yml up -d

# View logs
docker-compose -f docker-compose.fastapi.yml logs -f loan-decision-api

# Stop all services
docker-compose -f docker-compose.fastapi.yml down

# View service status
docker-compose -f docker-compose.fastapi.yml ps
```

---

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest test_fastapi_main.py -v

# Run specific test
pytest test_fastapi_main.py::test_health_check_endpoint -v

# Run with coverage
pytest test_fastapi_main.py --cov=main --cov-report=html
```

### Manual Testing with Client Example

```bash
# Run the example client
python fastapi_client_example.py
```

This will demonstrate:
- Health check
- Application submission
- Validation errors
- Decision filtering
- Pagination
- Error handling

### Test with cURL

```bash
# Health check
curl http://localhost:8000/health

# Submit application (create request.json first)
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d @request.json

# Get status
curl http://localhost:8000/api/v1/applications/APP-20240619-000001

# Get decisions
curl "http://localhost:8000/api/v1/decisions?page=1&page_size=10"
```

### Test with Python

```python
import requests

# Health check
resp = requests.get("http://localhost:8000/health")
print(resp.json())

# Submit application
app_data = {...}  # See FASTAPI_MAIN_GUIDE.md for structure
resp = requests.post("http://localhost:8000/api/v1/applications", json=app_data)
app_id = resp.json()["application_id"]

# Check status
resp = requests.get(f"http://localhost:8000/api/v1/applications/{app_id}")
print(resp.json())

# Get decisions
resp = requests.get("http://localhost:8000/api/v1/decisions")
print(resp.json())
```

---

## Interactive API Documentation

Once running, access the interactive documentation:

### Swagger UI
- **URL:** http://localhost:8000/docs
- **Features:**
  - Try API endpoints
  - View request/response schemas
  - See parameter descriptions
  - Auto-generated from code

### ReDoc
- **URL:** http://localhost:8000/redoc
- **Features:**
  - Static API documentation
  - Organized by tags
  - Detailed model definitions

### OpenAPI Schema
- **URL:** http://localhost:8000/openapi.json
- **Use:** Import into API tools (Postman, Insomnia, etc.)

---

## Logging

### View Logs

Logs are printed to console by default with format:
```
2024-06-19 10:30:00,000 - main - INFO - Processing loan application
```

### Log Levels

- `INFO` - Normal operations
- `WARNING` - Potential issues
- `ERROR` - Error conditions

### Change Log Level

Update in `.env`:
```env
LOG_LEVEL=DEBUG  # More verbose
LOG_LEVEL=WARNING  # Less verbose
```

---

## Error Handling

### Common Error Codes

| Status | Meaning |
|--------|---------|
| 200 | OK - Request successful |
| 202 | Accepted - Request queued for processing |
| 404 | Not Found - Resource not found |
| 422 | Validation Error - Invalid request data |
| 500 | Server Error - Internal error |

### Error Response Format

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "timestamp": "2024-06-19T10:30:00.000000",
  "request_id": "req-12345"
}
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Change `API_PORT` in `.env` |
| Module not found | Run `pip install -r requirements.txt` |
| CORS errors | Check `FRONTEND_URL` in `.env` |
| Database errors | Verify database connection in `.env` |

---

## CORS Configuration

By default, the following origins are allowed:

- http://localhost
- http://localhost:3000
- http://localhost:8000
- http://127.0.0.1
- http://127.0.0.1:3000
- http://127.0.0.1:8000
- Value of `FRONTEND_URL` environment variable

### Add Custom Origin

Edit `main.py` in the `CORSMiddleware` section:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://yourdomain.com",  # Add here
    ],
    ...
)
```

---

## Performance Tips

### Increase Workers (Production)

```bash
# Use 4 workers for 4-core CPU
uvicorn main:app --workers 4

# Or with Gunicorn
gunicorn main:app -w 4
```

### Enable Caching

For repeated status checks, implement Redis caching:

```python
# In future enhancement
from redis import Redis
cache = Redis(host='localhost', port=6379)
```

### Database Connection Pooling

If using PostgreSQL:

```python
# In future enhancement
from sqlalchemy.pool import QueuePool
engine = create_engine(DATABASE_URL, poolclass=QueuePool, pool_size=10)
```

### Pagination

- Default page size: 10
- Maximum page size: 100
- Use larger pages for bulk operations

---

## Monitoring

### Health Check Endpoint

```bash
# Use for load balancer health checks
curl http://localhost:8000/health

# Response indicates system health
```

### Metrics (Future Enhancement)

Plan to add Prometheus metrics:

```python
# Installation
pip install prometheus-client

# Export metrics endpoint
GET /metrics
```

### Application Logs

Monitor logs for:
- Failed validations
- Processing errors
- Database issues
- Orchestrator status

---

## Integration with LangGraph Orchestrator

The application automatically initializes the LangGraph orchestrator on startup.

### Enable Processing

In `submit_loan_application`, uncomment:

```python
if app_state.orchestrator:
    await app_state.orchestrator.process_application(app_id)
```

### Custom Orchestrator

Replace orchestrator import in startup event:

```python
from your_custom_orchestrator import create_orchestrator

app_state.orchestrator = create_orchestrator()
```

---

## Security Checklist

- [x] Input validation (Pydantic models)
- [x] CORS configuration
- [x] Error handling (no sensitive data leaked)
- [x] Email/phone validation
- [x] Rate limiting (future)
- [ ] Authentication/Authorization
- [ ] HTTPS/SSL
- [ ] API key management
- [ ] Database encryption

---

## Deployment

### Production Checklist

- [ ] Set `DEBUG=false` in `.env`
- [ ] Use strong `ANTHROPIC_API_KEY`
- [ ] Configure proper `FRONTEND_URL`
- [ ] Set up SSL/TLS certificate
- [ ] Configure reverse proxy (nginx)
- [ ] Set up logging infrastructure
- [ ] Configure backup strategy
- [ ] Set up monitoring/alerts

### Recommended Stack

```
┌─────────────────┐
│  Client/Browser │
│   (CORS)        │
└────────┬────────┘
         │
┌────────▼────────┐
│  nginx (SSL)    │
│  (Port 80/443)  │
└────────┬────────┘
         │
┌────────▼──────────────┐
│  FastAPI Application  │
│  (4+ workers)         │
└────────┬──────────────┘
         │
┌────────▼────────┐
│  PostgreSQL DB  │
│  (with backups) │
└─────────────────┘
```

---

## Support

### Documentation

- **API Guide:** See `FASTAPI_MAIN_GUIDE.md`
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **Swagger UI:** http://localhost:8000/docs

### Debugging

```bash
# Run in debug mode
DEBUG=true python main.py

# Watch logs in real-time
docker-compose -f docker-compose.fastapi.yml logs -f

# Check service health
curl http://localhost:8000/health
```

### Issues & Troubleshooting

1. Check `.env` configuration
2. Review application logs
3. Verify network connectivity
4. Check database status
5. Test with `fastapi_client_example.py`

---

## Next Steps

1. **Local Development:**
   - Run `python main.py`
   - Access http://localhost:8000/docs
   - Test with `fastapi_client_example.py`

2. **Testing:**
   - Run `pytest test_fastapi_main.py -v`
   - Fix any failing tests

3. **Integration:**
   - Connect to actual database
   - Integrate with LangGraph orchestrator
   - Implement async processing

4. **Deployment:**
   - Containerize with Docker
   - Deploy with Docker Compose
   - Set up monitoring and logging

---

## License

This project is part of the Loan Decision System.

For more information, see `README.md` in the project root.
