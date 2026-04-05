# app/main.py

import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.documentation_agent import DiagnosticOrchestrator
from tools.safety_gate import SafetyGate

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Clinical AI — Family Medicine",
    page_icon="🩺",
    layout="wide"
)

# ─────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────
st.title("🩺 Clinical AI — Family Medicine Assistant")
st.caption(
    "AI-powered clinical decision support. "
    "All outputs require review by a qualified clinician."
)
st.divider()

# ─────────────────────────────────────────
#  SIDEBAR — PATIENT DETAILS
# ─────────────────────────────────────────
with st.sidebar:
    st.header("Patient Details")

    case_id = st.text_input("Case ID", value="CASE001")
    age     = st.number_input("Age", min_value=1, max_value=120, value=44)
    sex     = st.selectbox("Sex", ["F", "M", "Other"])

    st.subheader("Past Medical History")
    pmh_input = st.text_area(
        "One condition per line",
        placeholder="Hypertension\nHypercholesterolaemia",
        height=100
    )

    st.subheader("Current Medications")
    med_input = st.text_area(
        "One medication per line",
        placeholder="Amlodipine 5mg OD\nAtorvastatin 20mg ON",
        height=100
    )

    st.subheader("Vitals (optional)")
    col1, col2 = st.columns(2)
    with col1:
        hr = st.text_input("HR (bpm)", placeholder="88")
        bp = st.text_input("BP",       placeholder="148/92")
    with col2:
        temp = st.text_input("Temp °C", placeholder="37.2")
        sats = st.text_input("O2 Sats", placeholder="98%")

# ─────────────────────────────────────────
#  MAIN — CONSULTATION NOTE INPUT
# ─────────────────────────────────────────
st.subheader("Consultation Note")
raw_input = st.text_area(
    "Enter the patient presentation",
    placeholder="e.g. 4-month history of fatigue, weight gain, feeling cold all the time, constipation and low mood. Hair has become thin and dry.",
    height=150
)

analyse = st.button("Analyse Case", type="primary", use_container_width=True)

# ─────────────────────────────────────────
#  PROCESS AND DISPLAY
# ─────────────────────────────────────────
if analyse:
    if not raw_input.strip():
        st.warning("Please enter a consultation note before analysing.")
        st.stop()

    # parse inputs
    pmh         = [p.strip() for p in pmh_input.split("\n") if p.strip()]
    medications = [m.strip() for m in med_input.split("\n") if m.strip()]
    vitals      = {}
    if hr:   vitals["hr"]   = hr
    if bp:   vitals["bp"]   = bp
    if temp: vitals["temp"] = temp
    if sats: vitals["sats"] = sats

    # run pipeline
    with st.spinner("Running clinical AI pipeline..."):
        try:
            orch   = DiagnosticOrchestrator()
            report = orch.run(
                raw_input=raw_input,
                case_id=case_id,
                age=age,
                sex=sex,
                pmh=pmh,
                medications=medications,
                vitals=vitals if vitals else None
            )
            gate   = SafetyGate()
            report = gate.validate(report)

        except Exception as e:
            st.error(f"Pipeline error: {str(e)}")
            st.stop()

    st.divider()

    # ── Urgent Alerts ──
    if report.urgent_alerts:
        st.subheader("⚠️ Urgent Alerts")
        for alert in report.urgent_alerts:
            st.error(alert)
    else:
        st.success("No urgent alerts — no cannot-miss diagnoses detected")

    st.divider()

    # ── Three column output ──
    col_diff, col_tests, col_audit = st.columns([2, 2, 1])

    with col_diff:
        st.subheader("Ranked Differentials")
        if report.differentials:
            for i, diff in enumerate(report.differentials, 1):
                confidence_pct = int(diff.confidence * 100)
                with st.expander(
                    f"{i}. {diff.diagnosis} — {confidence_pct}%",
                    expanded=(i == 1)
                ):
                    if confidence_pct > 0:
                        st.progress(diff.confidence)
                    if diff.reasoning:
                        st.write(diff.reasoning)
                    if diff.red_flags:
                        for rf in diff.red_flags:
                            st.warning(rf)
        else:
            st.info("No differentials extracted — try a more detailed consultation note.")

    with col_tests:
        st.subheader("Recommended Investigations")
        if report.test_recommendations:
            for i, test in enumerate(report.test_recommendations, 1):
                priority_color = {
                    "urgent":  "🔴",
                    "soon":    "🟡",
                    "routine": "🟢"
                }.get(test.priority, "⚪")

                st.markdown(f"**{i}. {priority_color} {test.test_name}**")
                if test.rationale:
                    st.caption(test.rationale)
                st.write("")
        else:
            st.info("No investigations extracted.")

    with col_audit:
        st.subheader("Audit Trail")
        for entry in report.audit_trail:
            status = "✅" if entry.success else "❌"
            st.markdown(f"{status} `{entry.step}`")
        st.caption(f"Case: {report.case_id}")
        st.caption(f"Model: qwen:1.8b")

    st.divider()

    # ── Disclaimer ──
    st.warning(f"⚠️ {report.disclaimer}")