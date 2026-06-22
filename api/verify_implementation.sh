#!/bin/bash

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================"
echo "Loan Application API - Verification"
echo "================================"
echo ""

# Check Python version
echo -n "Checking Python version... "
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if [[ $python_version > "3.7" ]]; then
    echo -e "${GREEN}✓${NC} Python $python_version"
else
    echo -e "${RED}✗${NC} Python version too old"
    exit 1
fi

# Check required packages
echo ""
echo "Checking required packages..."
packages=("fastapi" "pydantic" "httpx" "uvicorn")
for package in "${packages[@]}"; do
    if python3 -c "import ${package}" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $package"
    else
        echo -e "  ${RED}✗${NC} $package (not installed)"
    fi
done

# Check file structure
echo ""
echo "Checking file structure..."
files=(
    "loan_application_api.py"
    "loan_api_client.py"
    "test_loan_api.py"
    "example_client_usage.py"
    "README.md"
    "LOAN_API_GUIDE.md"
    "IMPLEMENTATION_SUMMARY.md"
    "requirements.txt"
    "Dockerfile"
    "docker-compose.yml"
)

for file in "${files[@]}"; do
    if [ -f "/home/ubuntu/Desktop/demo/api/$file" ]; then
        size=$(du -h "/home/ubuntu/Desktop/demo/api/$file" | cut -f1)
        echo -e "  ${GREEN}✓${NC} $file ($size)"
    else
        echo -e "  ${RED}✗${NC} $file (missing)"
    fi
done

# Check Python syntax
echo ""
echo "Checking Python syntax..."
python3 -m py_compile /home/ubuntu/Desktop/demo/api/loan_application_api.py 2>/dev/null && \
    echo -e "  ${GREEN}✓${NC} loan_application_api.py" || \
    echo -e "  ${RED}✗${NC} loan_application_api.py"

python3 -m py_compile /home/ubuntu/Desktop/demo/api/loan_api_client.py 2>/dev/null && \
    echo -e "  ${GREEN}✓${NC} loan_api_client.py" || \
    echo -e "  ${RED}✗${NC} loan_api_client.py"

# Verify key classes
echo ""
echo "Verifying key classes and functions..."

# Check loan_application_api.py
python3 << 'PYTHON_CHECK'
import sys
sys.path.insert(0, '/home/ubuntu/Desktop/demo/api')

try:
    from loan_application_api import (
        app,
        LoanApplicationRequest,
        LoanDecisionResponse,
        DecisionFactor,
        ErrorResponse
    )
    print("  ✓ LoanApplicationRequest")
    print("  ✓ LoanDecisionResponse")
    print("  ✓ DecisionFactor")
    print("  ✓ ErrorResponse")
    print("  ✓ FastAPI app")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)
PYTHON_CHECK

# Check client classes
python3 << 'PYTHON_CHECK'
import sys
sys.path.insert(0, '/home/ubuntu/Desktop/demo/api')

try:
    from loan_api_client import (
        LoanApplicationClient,
        SyncLoanApplicationClient,
        submit_loan_application_sync
    )
    print("  ✓ LoanApplicationClient")
    print("  ✓ SyncLoanApplicationClient")
    print("  ✓ submit_loan_application_sync")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)
PYTHON_CHECK

# Summary
echo ""
echo "================================"
echo "Verification Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Start API server:"
echo "   python -m uvicorn loan_application_api:app --reload"
echo ""
echo "2. Access documentation:"
echo "   Swagger: http://localhost:8000/api/docs"
echo "   ReDoc: http://localhost:8000/api/redoc"
echo ""
echo "3. Run tests:"
echo "   pytest test_loan_api.py -v"
echo ""
echo "4. Try examples:"
echo "   python example_client_usage.py"
echo ""
