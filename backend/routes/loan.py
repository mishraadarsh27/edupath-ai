from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_conn
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class LoanCalcPayload(BaseModel):
    course_cost: float
    own_contribution: float
    income: float

@router.post("/calculate")
def calculate_loan(payload: LoanCalcPayload):
    """Calculates loan eligibility and compares bank offers."""
    req_amount = payload.course_cost - payload.own_contribution
    
    # Eligibility Logic
    annual_income = payload.income * 12
    if req_amount <= 0:
        eligibility = "Fully Covered"
    elif annual_income > req_amount * 0.3:
        eligibility = "Highly Eligible"
    elif annual_income > req_amount * 0.15:
        eligibility = "Moderate Eligibility"
    else:
        eligibility = "Low Eligibility (Joint Cosigner Recommended)"
        
    def calc_emi(p, rate_annual, months=120):
        if p <= 0: return 0
        r = rate_annual / 12 / 100
        return p * r * ((1 + r)**months) / (((1 + r)**months) - 1)

    return {
        "required_amount": req_amount,
        "eligibility": eligibility,
        "offers": [
            {"bank": "SBI", "rate": "11.15%", "emi": round(calc_emi(req_amount, 11.15)), "type": "Public Sector"},
            {"bank": "HDFC Credila", "rate": "12.5%", "emi": round(calc_emi(req_amount, 12.5)), "type": "Private/NBFC"},
            {"bank": "Axis Bank", "rate": "13.5%", "emi": round(calc_emi(req_amount, 13.5)), "type": "Private Sector"}
        ]
    }

class LoanApplyPayload(BaseModel):
    student_id: int
    loan_amount: float
    
@router.post("/apply")
def apply_loan(payload: LoanApplyPayload):
    """Submits a loan application request to the database."""
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO loan_applications (student_id, loan_amount) VALUES (?, ?)', 
                          (payload.student_id, payload.loan_amount))
            return {"status": "success", "message": "Application submitted! A consultant will contact you."}
    except Exception as e:
        logger.error(f"Loan application error: {e}")
        raise HTTPException(status_code=500, detail="Error submitting application")
