"""
Flask-based UI for Loan Approval System
Simpler alternative to Streamlit
"""

from flask import Flask, render_template, request, jsonify
from loan_orchestrator import compile_loan_orchestrator, execute_application
from loan_orchestrator import ApplicantProfile, FinancialData
import json
from datetime import datetime

app = Flask(__name__)

# Initialize orchestrator
orchestrator = compile_loan_orchestrator()

# Store results in memory
results_history = []

@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')

@app.route('/api/submit', methods=['POST'])
def submit_application():
    """Submit loan application"""
    try:
        data = request.json

        # Create profile
        profile = ApplicantProfile(
            applicant_id=data.get('applicant_id', 'APP_UNKNOWN'),
            name=data.get('name', 'Unknown'),
            age=int(data.get('age', 0)),
            employment_status=data.get('employment_status', 'employed'),
            employment_years=float(data.get('employment_years', 0)),
            education_level=data.get('education_level', 'bachelor'),
            credit_score=int(data.get('credit_score', 0)),
            existing_loans=int(data.get('existing_loans', 0))
        )

        # Create financial data
        annual_income = float(data.get('annual_income', 1))
        total_liabilities = float(data.get('total_liabilities', 0)) if 'total_liabilities' in data else float(data.get('debt_to_income_ratio', 0))

        # Calculate debt-to-income ratio: (total debt / annual income)
        dti = total_liabilities / annual_income if annual_income > 0 else 0

        financial = FinancialData(
            annual_income=annual_income,
            monthly_expenses=float(data.get('monthly_expenses', 0)),
            savings=float(data.get('savings', 0)),
            debt_to_income_ratio=dti
        )

        # Execute application
        result = execute_application(
            orchestrator,
            profile.applicant_id,
            profile,
            financial
        )

        # Format response
        loan_decision = result.get('loan_decision', {})
        compliance_result = result.get('compliance_result', {})

        # Extract decision info
        decision = str(loan_decision.decision).split('.')[-1] if hasattr(loan_decision, 'decision') else str(result.get('status', 'unknown')).split('.')[-1]
        score = loan_decision.decision_score if hasattr(loan_decision, 'decision_score') else 0
        approval_prob = loan_decision.approval_probability if hasattr(loan_decision, 'approval_probability') else 0
        compliance_check = compliance_result.is_compliant if hasattr(compliance_result, 'is_compliant') else False

        response = {
            'applicant_id': profile.applicant_id,
            'name': profile.name,
            'decision': decision,
            'score': round(score, 2),
            'confidence': round(approval_prob * 100, 1),
            'key_factors': [loan_decision.rationale] if hasattr(loan_decision, 'rationale') else [],
            'compliance': compliance_check,
            'timestamp': datetime.now().isoformat()
        }

        # Store in history
        results_history.append(response)

        return jsonify({
            'success': True,
            'result': response
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get application history"""
    return jsonify({
        'total': len(results_history),
        'history': results_history[-50:]  # Last 50
    })

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get statistics"""
    if not results_history:
        return jsonify({
            'total': 0,
            'approved': 0,
            'rejected': 0,
            'review': 0,
            'approval_rate': 0
        })

    approved = sum(1 for r in results_history if r['decision'].lower() == 'approved')
    rejected = sum(1 for r in results_history if r['decision'].lower() == 'rejected')
    review = sum(1 for r in results_history if r['decision'].lower() == 'manual_review')

    return jsonify({
        'total': len(results_history),
        'approved': approved,
        'rejected': rejected,
        'review': review,
        'approval_rate': round((approved / len(results_history) * 100) if results_history else 0, 1)
    })

if __name__ == '__main__':
    print("🚀 Flask Loan Approval System Starting...")
    print("📱 Open browser: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
