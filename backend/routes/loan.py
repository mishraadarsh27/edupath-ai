from fastapi import APIRouter
from pydantic import BaseModel
from database import get_db

router = APIRouter()

class LoanCalcPayload(BaseModel):
    course_cost: float
    own_contribution: float
    income: float

@router.post("/calculate")
def calculate_loan(payload: LoanCalcPayload):
    req_amount = payload.course_cost - payload.own_contribution
    
    if req_amount <= 0:
        eligibility = "Eligible" # Don't need a loan, but okay
    elif payload.income * 12 > req_amount * 0.3:
        eligibility = "Eligible"
    elif payload.income * 12 > req_amount * 0.1:
        eligibility = "Partially Eligible"
    else:
        eligibility = "Not Eligible"
        
    def calc_emi(p, rate_annual, months=120):
        if p <= 0: return 0
        r = rate_annual / 12 / 100
        return p * r * ((1 + r)**months) / (((1 + r)**months) - 1)

    sbi_emi = calc_emi(req_amount, 11.15)
    hdfc_emi = calc_emi(req_amount, 12.5)
    axis_emi = calc_emi(req_amount, 13.5)
    
    return {
        "required_amount": req_amount,
        "eligibility": eligibility,
        "offers": [
            {"bank": "SBI", "rate": "11.15%", "emi": round(sbi_emi), "fee": "0%"},
            {"bank": "HDFC Credila", "rate": "12.5%", "emi": round(hdfc_emi), "fee": "1%"},
            {"bank": "Axis Bank", "rate": "13.5%", "emi": round(axis_emi), "fee": "0.5%"}
        ]
    }

class LoanApplyPayload(BaseModel):
    student_id: int
    loan_amount: float
    
@router.post("/apply")
def apply_loan(payload: LoanApplyPayload):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO loan_applications (student_id, loan_amount) VALUES (?, ?)', (payload.student_id, payload.loan_amount))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Application submitted successfully"}
