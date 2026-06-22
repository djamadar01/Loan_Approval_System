#!/usr/bin/env python3
"""
Verification script for Loan Application API implementation.
"""

import sys
import os
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(text)
    print("=" * 50)

def check_files():
    """Check if all required files exist."""
    print_header("File Structure Check")
    
    api_dir = Path("/home/ubuntu/Desktop/demo/api")
    required_files = {
        "loan_application_api.py": "Main FastAPI application",
        "loan_api_client.py": "Client libraries",
        "test_loan_api.py": "Test suite",
        "example_client_usage.py": "Usage examples",
        "README.md": "Quick start guide",
        "LOAN_API_GUIDE.md": "Comprehensive documentation",
        "IMPLEMENTATION_SUMMARY.md": "Implementation details",
        "requirements.txt": "Python dependencies",
        "Dockerfile": "Docker configuration",
        "docker-compose.yml": "Compose configuration"
    }
    
    all_exist = True
    for filename, description in required_files.items():
        filepath = api_dir / filename
        exists = filepath.exists()
        status = "✓" if exists else "✗"
        size = ""
        if exists:
            size = f" ({filepath.stat().st_size:,} bytes)"
        print(f"  {status} {filename}{size}")
        print(f"      {description}")
        all_exist = all_exist and exists
    
    return all_exist

def check_python_modules():
    """Check Python module imports."""
    print_header("Python Module Check")
    
    sys.path.insert(0, '/home/ubuntu/Desktop/demo/api')
    sys.path.insert(0, '/home/ubuntu/Desktop/demo')
    
    modules_to_check = {
        "FastAPI Application": [
            ("loan_application_api", "LoanApplicationRequest"),
            ("loan_application_api", "LoanDecisionResponse"),
            ("loan_application_api", "DecisionFactor"),
            ("loan_application_api", "ErrorResponse"),
        ],
        "Client Library": [
            ("loan_api_client", "LoanApplicationClient"),
            ("loan_api_client", "SyncLoanApplicationClient"),
            ("loan_api_client", "submit_loan_application_sync"),
        ]
    }
    
    all_ok = True
    for section, items in modules_to_check.items():
        print(f"\n{section}:")
        for module_name, class_name in items:
            try:
                module = __import__(module_name)
                obj = getattr(module, class_name)
                print(f"  ✓ {module_name}.{class_name}")
            except (ImportError, AttributeError) as e:
                print(f"  ✗ {module_name}.{class_name}")
                print(f"      Error: {e}")
                all_ok = False
    
    return all_ok

def check_endpoints():
    """Check endpoint definitions."""
    print_header("Endpoint Check")
    
    sys.path.insert(0, '/home/ubuntu/Desktop/demo/api')
    
    endpoints = {
        "GET /health": "Health check endpoint",
        "POST /submit-application": "Main loan application endpoint",
        "POST /test-application": "Test endpoint for development"
    }
    
    try:
        from loan_application_api import app
        
        routes = {}
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method != 'HEAD':
                        key = f"{method} {route.path}"
                        routes[key] = route
        
        all_ok = True
        for endpoint, description in endpoints.items():
            exists = endpoint in routes
            status = "✓" if exists else "✗"
            print(f"  {status} {endpoint}")
            print(f"      {description}")
            all_ok = all_ok and exists
        
        return all_ok
    except Exception as e:
        print(f"  ✗ Error checking endpoints: {e}")
        return False

def check_validation():
    """Check request validation."""
    print_header("Validation Check")
    
    sys.path.insert(0, '/home/ubuntu/Desktop/demo/api')
    sys.path.insert(0, '/home/ubuntu/Desktop/demo')
    
    try:
        from loan_application_api import LoanApplicationRequest
        from pydantic import ValidationError
        
        # Valid request
        valid_data = {
            "applicant_id": "TEST-001",
            "profile": {
                "name": "Test User",
                "age": 35,
                "employment_status": "full_time",
                "employment_years": 5,
                "education_level": "bachelor",
                "annual_income": 75000,
                "monthly_expenses": 2500,
                "savings": 15000,
                "existing_loans": 1
            },
            "credit_score": 720,
            "loan_amount": 25000,
            "tenure": 60,
            "liabilities": 10000,
            "location": "New York, NY"
        }
        
        # Test valid request
        try:
            req = LoanApplicationRequest(**valid_data)
            print("  ✓ Valid request acceptance")
        except Exception as e:
            print(f"  ✗ Valid request rejected: {e}")
            return False
        
        # Test invalid credit score
        try:
            invalid_data = valid_data.copy()
            invalid_data["credit_score"] = 200
            req = LoanApplicationRequest(**invalid_data)
            print("  ✗ Invalid credit score accepted")
            return False
        except ValidationError:
            print("  ✓ Invalid credit score rejection")
        
        # Test invalid age
        try:
            invalid_data = valid_data.copy()
            invalid_data["profile"]["age"] = 15
            req = LoanApplicationRequest(**invalid_data)
            print("  ✗ Invalid age accepted")
            return False
        except ValidationError:
            print("  ✓ Invalid age rejection")
        
        # Test missing profile field
        try:
            invalid_data = valid_data.copy()
            invalid_data["profile"].pop("annual_income")
            req = LoanApplicationRequest(**invalid_data)
            print("  ✗ Missing profile field accepted")
            return False
        except ValidationError:
            print("  ✓ Missing profile field rejection")
        
        return True
    except Exception as e:
        print(f"  ✗ Error during validation check: {e}")
        return False

def main():
    """Run all checks."""
    print("\n" + "=" * 50)
    print("LOAN APPLICATION API - IMPLEMENTATION VERIFICATION")
    print("=" * 50)
    
    results = {
        "Files": check_files(),
        "Python Modules": check_python_modules(),
        "Endpoints": check_endpoints(),
        "Validation": check_validation()
    }
    
    print_header("VERIFICATION SUMMARY")
    
    for check, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {check}")
    
    all_passed = all(results.values())
    
    print_header("NEXT STEPS")
    print("""
1. Start the API server:
   cd /home/ubuntu/Desktop/demo/api
   python -m uvicorn loan_application_api:app --reload

2. Access the interactive documentation:
   Swagger UI: http://localhost:8000/api/docs
   ReDoc: http://localhost:8000/api/redoc

3. Test the API:
   - Use the Swagger UI to submit a test application
   - Or run: python example_client_usage.py

4. Run the test suite:
   pytest test_loan_api.py -v

5. Review the documentation:
   - README.md - Quick start
   - LOAN_API_GUIDE.md - Full API reference
   - IMPLEMENTATION_SUMMARY.md - Implementation details
""")
    
    print("=" * 50)
    if all_passed:
        print("STATUS: ✓ ALL CHECKS PASSED - READY FOR USE")
    else:
        print("STATUS: ✗ SOME CHECKS FAILED - REVIEW ABOVE")
    print("=" * 50 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
