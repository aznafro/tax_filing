import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ultimate 50-State Tax Master 2025", layout="wide", initial_sidebar_state="expanded")

# --- FULL 50-STATE TAX DATA (2025 estimates & real where available) ---
STATE_RULES = {
    "Alabama": {"type": "progressive", "deduction": 3000, "brackets": [(0, 500, 0.02), (500, 3000, 0.04), (3000, float('inf'), 0.05)]},
    "Alaska": {"type": "none"},
    "Arizona": {"type": "flat", "rate": 0.025, "deduction": 0},
    "Arkansas": {"type": "progressive", "deduction": 2200, "brackets": [(0, 4100, 0.02), (4100, 8100, 0.039), (8100, float('inf'), 0.049)]},
    "California": {"type": "progressive", "deduction": 0, "brackets": [
        (0, 11000, 0.01), (11000, 26000, 0.02), (26000, 41000, 0.04), (41000, 57000, 0.06),
        (57000, 72000, 0.08), (72000, 368000, 0.093), (368000, 441000, 0.103),
        (441000, 736000, 0.113), (736000, 1000000, 0.123), (1000000, float('inf'), 0.133)]},
    "Colorado": {"type": "flat", "rate": 0.044, "deduction": 0},
    "Connecticut": {"type": "progressive", "deduction": 0, "brackets": [
        (0, 10000, 0.03), (10000, 50000, 0.05), (50000, 100000, 0.055), (100000, 200000, 0.06),
        (200000, 250000, 0.065), (250000, 500000, 0.069), (500000, float('inf'), 0.0699)]},
    "Delaware": {"type": "progressive", "deduction": 3250, "brackets": [(0, 2000, 0), (2000, 5000, 0.022), (5000, 10000, 0.039), (10000, 20000, 0.048), (20000, 25000, 0.052), (25000, 60000, 0.0555), (60000, float('inf'), 0.066)]},
    "Florida": {"type": "none"},
    "Georgia": {"type": "flat", "rate": 0.0549, "deduction": 5000},
    "Hawaii": {"type": "progressive", "deduction": 2200, "brackets": [(0, 2400, 0.014), (2400, 4800, 0.032), (4800, 9600, 0.055), (9600, 14400, 0.064), (14400, 19200, 0.068), (19200, 24000, 0.072), (24000, 36000, 0.076), (36000, 48000, 0.079), (48000, 150000, 0.0825), (150000, 175000, 0.09), (175000, 200000, 0.10), (200000, float('inf'), 0.11)]},
    "Idaho": {"type": "flat", "rate": 0.058, "deduction": 0},
    "Illinois": {"type": "flat", "rate": 0.0495, "deduction": 2775},
    "Indiana": {"type": "flat", "rate": 0.0315, "deduction": 1000},
    "Iowa": {"type": "progressive", "deduction": 0, "brackets": [(0, 1740, 0.045), (1740, 3480, 0.06), (3480, float('inf'), 0.064)]},
    "Kansas": {"type": "progressive", "deduction": 3000, "brackets": [(0, 15000, 0.031), (15000, 30000, 0.0525), (30000, float('inf'), 0.057)]},
    "Kentucky": {"type": "flat", "rate": 0.045, "deduction": 0},
    "Louisiana": {"type": "progressive", "deduction": 4500, "brackets": [(0, 12500, 0.0185), (12500, 50000, 0.035), (50000, float('inf'), 0.0425)]},
    "Maine": {"type": "progressive", "deduction": 0, "brackets": [(0, 25000, 0.058), (25000, 50000, 0.0675), (50000, float('inf'), 0.0715)]},
    "Maryland": {"type": "progressive", "deduction": 2400, "brackets": [(0, 1000, 0.02), (1000, 2000, 0.03), (2000, 3000, 0.04), (3000, 100000, 0.0475), (100000, 125000, 0.05), (125000, 150000, 0.0525), (150000, 250000, 0.055), (250000, float('inf'), 0.0575)]},
    "Massachusetts": {"type": "flat", "rate": 0.05, "deduction": 4400},
    "Michigan": {"type": "flat", "rate": 0.0425, "deduction": 0},
    "Minnesota": {"type": "progressive", "deduction": 13825, "brackets": [(0, 31000, 0.0535), (31000, 100000, 0.068), (100000, 183000, 0.0785), (183000, float('inf'), 0.0985)]},
    "Mississippi": {"type": "progressive", "deduction": 2300, "brackets": [(0, 5000, 0), (5000, 10000, 0.04), (10000, float('inf'), 0.05)]},
    "Missouri": {"type": "progressive", "deduction": 0, "brackets": [(0, 1000, 0.015), (1000, 2000, 0.02), (2000, 3000, 0.025), (3000, 4000, 0.03), (4000, 5000, 0.035), (5000, 6000, 0.04), (6000, 7000, 0.045), (7000, 8000, 0.05), (8000, 9000, 0.0525), (9000, float('inf'), 0.054)]},
    "Montana": {"type": "progressive", "deduction": 0, "brackets": [(0, 3400, 0.01), (3400, 5900, 0.02), (5900, 9000, 0.03), (9000, 12200, 0.04), (12200, 15700, 0.05), (15700, 20000, 0.06), (20000, float('inf'), 0.0675)]},
    "Nebraska": {"type": "progressive", "deduction": 0, "brackets": [(0, 3700, 0.0246), (3700, 22100, 0.0351), (22100, 35400, 0.0501), (35400, float('inf'), 0.0644)]},
    "Nevada": {"type": "none"},
    "New Hampshire": {"type": "none"},  # Only interest/dividends tax, not included
    "New Jersey": {"type": "progressive", "deduction": 0, "brackets": [(0, 20000, 0.014), (20000, 35000, 0.0175), (35000, 40000, 0.035), (40000, 75000, 0.05525), (75000, 500000, 0.0637), (500000, 1000000, 0.0897), (1000000, float('inf'), 0.1075)]},
    "New Mexico": {"type": "progressive", "deduction": 0, "brackets": [(0, 5500, 0.017), (5500, 11000, 0.032), (11000, 16000, 0.047), (16000, 210000, 0.049), (210000, float('inf'), 0.059)]},
    "New York": {"type": "progressive", "deduction": 8000, "brackets": [
        (0, 8500, 0.04), (8500, 11700, 0.045), (11700, 13900, 0.0525), (13900, 80650, 0.055), (80650, 215400, 0.06), (215400, 1077550, 0.0685), (1077550, 5000000, 0.0965), (5000000, 25000000, 0.103), (25000000, float('inf'), 0.109)]},
    "North Carolina": {"type": "flat", "rate": 0.0475, "deduction": 0},
    "North Dakota": {"type": "progressive", "deduction": 0, "brackets": [(0, 41775, 0.011), (41775, 101050, 0.0204), (101050, 198550, 0.0227), (198550, 246700, 0.0264), (246700, float('inf'), 0.029)]},
    "Ohio": {"type": "progressive", "deduction": 0, "brackets": [(0, 26050, 0), (26050, 46100, 0.02779), (46100, 92150, 0.03226), (92150, 115300, 0.03659), (115300, float('inf'), 0.0399)]},
    "Oklahoma": {"type": "progressive", "deduction": 6350, "brackets": [(0, 1000, 0.0025), (1000, 2500, 0.01), (2500, 3750, 0.02), (3750, 4900, 0.03), (4900, 7200, 0.04), (7200, float('inf'), 0.0475)]},
    "Oregon": {"type": "progressive", "deduction": 0, "brackets": [(0, 4100, 0.0475), (4100, 10250, 0.0675), (10250, 125000, 0.0875), (125000, float('inf'), 0.099)]},
    "Pennsylvania": {"type": "flat", "rate": 0.0307, "deduction": 0},
    "Rhode Island": {"type": "progressive", "deduction": 0, "brackets": [(0, 73200, 0.0375), (73200, 166950, 0.0475), (166950, float('inf'), 0.0599)]},
    "South Carolina": {"type": "progressive", "deduction": 0, "brackets": [(0, 3460, 0), (3460, 6920, 0.03), (6920, 10380, 0.04), (10380, 13840, 0.05), (13840, 17300, 0.06), (17300, float('inf'), 0.065)]},
    "South Dakota": {"type": "none"},
    "Tennessee": {"type": "none"},
    "Texas": {"type": "none"},
    "Utah": {"type": "flat", "rate": 0.0485, "deduction": 0},
    "Vermont": {"type": "progressive", "deduction": 0, "brackets": [(0, 45000, 0.035), (45000, 109000, 0.06), (109000, 208650, 0.0725), (208650, float('inf'), 0.0875)]},
    "Virginia": {"type": "progressive", "deduction": 0, "brackets": [(0, 3000, 0.02), (3000, 5000, 0.03), (5000, 17000, 0.05), (17000, float('inf'), 0.0575)]},
    "Washington": {"type": "none"},
    "West Virginia": {"type": "progressive", "deduction": 0, "brackets": [(0, 10000, 0.03), (10000, 25000, 0.04), (25000, 40000, 0.045), (40000, 60000, 0.06), (60000, float('inf'), 0.065)]},
    "Wisconsin": {"type": "progressive", "deduction": 0, "brackets": [(0, 13810, 0.035), (13810, 27620, 0.044), (27620, 30470, 0.053), (30470, float('inf'), 0.0765)]},
    "Wyoming": {"type": "none"},
}

# --- TAX CALCULATION ENGINE (unchanged from last working version) ---
# ... (keep your full calculate_taxes function here - same as before)

# --- SAVE / LOAD SESSION ---
session_file = "tax_session.json"

# --- 2. THE 2025 TAX ENGINE (Fully Improved & Accurate) ---
def calculate_taxes(p):
    # A. Self-Employment Tax (with 2025 SS wage base)
    se_base = p['side_hustle'] * 0.9235
    se_tax_ss = min(se_base, 176100) * 0.124  # 2025 Social Security cap
    se_tax_medicare = se_base * 0.029
    se_tax = se_tax_ss + se_tax_medicare

    # Half SE tax deduction (reduces AGI)
    se_deduction = se_tax / 2

    # B. OBBBA Tips & Overtime Deductions (capped + phaseout)
    phase_base = p['salary'] + p['side_hustle'] + p['st_gains'] + p['lt_gains'] + p['dividends']
    phase_limit = 300000 if p['status'] == "Married Filing Jointly" else 150000

    if phase_base < phase_limit:
        tips_ded = min(p['tips'], 25000)
        ot_cap = 25000 if p['status'] == "Married Filing Jointly" else 12500
        ot_ded = min(p['overtime'], ot_cap)
    else:
        tips_ded = ot_ded = 0

    # C. Adjusted Gross Income
    total_gross = p['salary'] + p['side_hustle'] + p['st_gains'] + p['lt_gains'] + p['dividends']
    agi = max(0, total_gross - p['pre_tax'] - p['student_loan'] - tips_ded - ot_ded - se_deduction)

    # D. Standard vs Itemized Deduction
    std_ded = 31500 if p['status'] == "Married Filing Jointly" else 15750
    itemized = p['mortgage'] + min(p['salt_paid'], 40000)  # OBBBA SALT cap
    final_deduction = max(std_ded, itemized)
    fed_taxable = max(0, agi - final_deduction)

    # E. Ordinary Federal Income Tax (2025 brackets)
    ordinary_tax = 0
    if p['status'] == "Married Filing Jointly":
        brackets = [(0, 23850, 0.10), (23850, 96950, 0.12), (96950, 206700, 0.22),
                    (206700, 394600, 0.24), (394600, 501050, 0.32), (501050, 751600, 0.35),
                    (751600, float('inf'), 0.37)]
    else:
        brackets = [(0, 11925, 0.10), (11925, 48475, 0.12), (48475, 103350, 0.22),
                    (103350, 197300, 0.24), (197300, 250525, 0.32), (250525, 626350, 0.35),
                    (626350, float('inf'), 0.37)]

    prev = 0
    for low, high, rate in brackets:
        if fed_taxable > prev:
            ordinary_tax += (min(fed_taxable, high) - prev) * rate
        prev = high if fed_taxable > high else fed_taxable

    # F. Long-Term Capital Gains Tax (0%/15%/20%)
    lt_gains_tax = 0
    if p['lt_gains'] > 0:
        if fed_taxable <= (96700 if p['status'] == "Married Filing Jointly" else 48350):
            lt_rate = 0.0
        elif fed_taxable <= (600050 if p['status'] == "Married Filing Jointly" else 300025):
            lt_rate = 0.15
        else:
            lt_rate = 0.20
        lt_gains_tax = p['lt_gains'] * lt_rate

    # G. Additional Medicare Tax (0.9%)
    add_medicare_threshold = 250000 if p['status'] == "Married Filing Jointly" else 200000
    earned = p['salary'] + p['side_hustle']
    add_medicare = max(0, earned - add_medicare_threshold) * 0.009

    # H. Net Investment Income Tax (3.8%)
    nii = p['st_gains'] + p['lt_gains'] + p['dividends']
    niit_threshold = 250000 if p['status'] == "Married Filing Jointly" else 200000
    niit = min(nii, max(0, agi - niit_threshold)) * 0.038

    # I. Child Tax Credit
    child_credit = p['kids'] * 2200

    # J. Final Federal Liability
    fed_liability = max(0, ordinary_tax + se_tax + lt_gains_tax + add_medicare + niit - child_credit)

    # K. State Tax
    rule = STATE_RULES.get(p['state'], {"type": "none"})
    state_ded = rule.get("deduction", 0)
    state_taxable = max(0, agi - state_ded)
    state_liability = 0
    if rule["type"] == "flat":
        state_liability = state_taxable * rule.get("rate", 0)
    elif rule["type"] == "progressive":
        prev = 0
        for low, high, rate in rule["brackets"]:
            if state_taxable > prev:
                state_liability += (min(state_taxable, high) - prev) * rate
            prev = high if state_taxable > high else state_taxable

    return fed_liability, state_liability, agi, fed_taxable, se_tax, lt_gains_tax, add_medicare, niit

# --- 5. PDF EXPORT FUNCTION (Final Working Version with fpdf2) ---
def create_pdf(df):
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Ultimate 2025 Tax Estimate Report", ln=True, align="C")
    pdf.ln(10)

    # Header
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(100, 10, "Category", border=1)
    pdf.cell(80, 10, "Amount ($)", border=1, ln=1, align="R")

    # Rows
    pdf.set_font("Helvetica", size=12)
    for _, row in df.iterrows():
        category = str(row["Category"])
        amount_str = str(row["Amount ($)"])
        pdf.cell(100, 10, category, border=1)
        pdf.cell(80, 10, amount_str, border=1, ln=1, align="R")

    # Handle bytearray → bytes (fpdf2 sometimes returns bytearray)
    pdf_data = pdf.output()
    if isinstance(pdf_data, bytearray):
        pdf_data = bytes(pdf_data)

    return pdf_data

def save_session(data):
    with open(session_file, "w") as f:
        json.dump(data, f)

def load_session():
    try:
        with open(session_file, "r") as f:
            return json.load(f)
    except:
        return None

# Load saved data if exists
saved = load_session() or {}

# --- SIDEBAR INPUTS ---
st.sidebar.header("🇺🇸 Life & Filing Setup")
state_choice = st.sidebar.selectbox("State of Residence", sorted(STATE_RULES.keys()))
status = st.sidebar.selectbox("Filing Status", ["Single", "Married Filing Jointly"], index=0 if not saved else ["Single", "Married Filing Jointly"].index(saved.get("status", "Single")))
kids = st.sidebar.number_input("Children Under 17 (Child Tax Credit)", min_value=0, value=saved.get("kids", 0))

st.sidebar.header("💰 Income Sources")
salary = st.sidebar.number_input("W-2 Salary", value=saved.get("salary", 80000))
side_hustle = st.sidebar.number_input("Self-Employment Profit (1099/Schedule C)", value=saved.get("side_hustle", 0))
tips = st.sidebar.number_input("Qualified Tips (OBBBA Deductible)", value=saved.get("tips", 0), help="Capped at $25k if under phaseout")
overtime = st.sidebar.number_input("Qualified Overtime Premium", value=saved.get("overtime", 0), help="Capped at $12.5k single / $25k joint")

st.sidebar.header("📑 Taxes Already Paid")
fed_wh = st.sidebar.number_input("Federal Tax Withheld", value=saved.get("fed_wh", 9000))
state_wh = st.sidebar.number_input("State Tax Withheld", value=saved.get("state_wh", 2000))

with st.sidebar.expander("🏠 Deductions & Investments"):
    pre_tax = st.number_input("401(k)/HSA/IRA Contributions", value=saved.get("pre_tax", 5000))
    student_loan = st.number_input("Student Loan Interest", value=saved.get("student_loan", 0))
    mortgage = st.number_input("Mortgage Interest", value=saved.get("mortgage", 0))
    salt_paid = st.number_input("State & Local Taxes Paid (SALT)", value=saved.get("salt_paid", 0))
    st_gains = st.number_input("Short-Term Capital Gains", value=saved.get("st_gains", 0))
    lt_gains = st.number_input("Long-Term Capital Gains/Distributions", value=saved.get("lt_gains", 0))
    divs = st.number_input("Dividends (incl. Qualified)", value=saved.get("divs", 0))

# Save button
if st.sidebar.button("💾 Save This Scenario"):
    save_data = {
        "state_choice": state_choice,
        "status": status,
        "kids": kids,
        "salary": salary,
        "side_hustle": side_hustle,
        "tips": tips,
        "overtime": overtime,
        "fed_wh": fed_wh,
        "state_wh": state_wh,
        "pre_tax": pre_tax,
        "student_loan": student_loan,
        "mortgage": mortgage,
        "salt_paid": salt_paid,
        "st_gains": st_gains,
        "lt_gains": lt_gains,
        "divs": divs  # renamed to match params key
    }
    save_session(save_data)
    st.sidebar.success("Scenario saved! Reload the app to see it load.")

# --- RUN CALCULATION ---
params = {
    'salary': salary,
    'side_hustle': side_hustle,
    'tips': tips,
    'overtime': overtime,
    'status': status,
    'kids': kids,
    'pre_tax': pre_tax,
    'student_loan': student_loan,
    'mortgage': mortgage,
    'salt_paid': salt_paid,
    'st_gains': st_gains or 0,
    'lt_gains': lt_gains or 0,
    'dividends': divs or 0,  # key must be 'dividends'
    'state': state_choice
}
fed_liab, state_liab, agi, taxable, se_tax, lt_tax, add_med, niit = calculate_taxes(params)
total_liab = fed_liab + state_liab
total_refund_due = (fed_wh + state_wh) - total_liab

# --- MAIN DASHBOARD ---
st.title("🛡️ Ultimate 50-State Tax Master 2025")
st.caption("Powered by OBBBA 2025 Rules • Estimates Only • Not for Filing")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Refund / (Due)", f"${total_refund_due:,.2f}" if total_refund_due >= 0 else f"(${ -total_refund_due:,.2f})", delta=None)
col2.metric("Federal Liability", f"${fed_liab:,.2f}", delta=f"${fed_wh - fed_liab:,.2f} vs Withheld")
col3.metric(f"{state_choice} State Liability", f"${state_liab:,.2f}", delta=f"${state_wh - state_liab:,.2f} vs Withheld")
col4.metric("Effective Tax Rate", f"{(total_liab / max(agi, 1) * 100):.1f}%")

st.markdown("---")
st.subheader("📊 Detailed Tax Breakdown")

display_state = state_choice
df = pd.DataFrame({
    "Category": [
        "Adjusted Gross Income (AGI)",
        "Federal Taxable Income",
        "Self-Employment Tax",
        "Ordinary Federal Income Tax",
        "Long-Term Gains Tax (0-20%)",
        "Additional Medicare Tax (0.9%)",
        "Net Investment Income Tax (3.8%)",
        "Child Tax Credit (Reduction)",
        f"{display_state} State Tax",
        "Total Tax Liability"
    ],
    "Amount ($)": [
        agi,
        taxable,
        se_tax,
        fed_liab - se_tax - lt_tax - add_med - niit - (params['kids'] * 2200),
        lt_tax,
        add_med,
        niit,
        params['kids'] * 2200,  # Positive
        state_liab,
        total_liab
    ]
}).style.format({"Amount ($)": "${:,.2f}"})

st.table(df)

# --- EXPORTS ---
st.markdown("---")
st.subheader("📥 Export Your Report")

# Keep your working create_pdf function here (with Helvetica + bytearray fix)

col_ex1, col_ex2 = st.columns(2)
with col_ex1:
    # df.data gives the raw DataFrame without Streamlit styling
    pdf_bytes = create_pdf(df.data)
    st.download_button(
        "📄 Download PDF Report",
        data=pdf_bytes,
        file_name=f"Tax_Estimate_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )

with col_ex2:
    excel_data = BytesIO()
    df.data.to_excel(excel_data, index=False)
    excel_data.seek(0)
    st.download_button("📈 Download Excel", data=excel_data.getvalue(), file_name=f"Tax_Data_{datetime.now().strftime('%Y%m%d')}.xlsx")

st.info("💡 Tip: Save your scenario with the button in the sidebar to return later!")

# --- FINAL TOUCH ---
st.markdown("---")
st.caption("Built with ❤️ using Streamlit • OBBBA 2025 estimates • Always verify with a tax professional")
