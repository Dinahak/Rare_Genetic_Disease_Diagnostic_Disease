import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.models import DiagnosticReport, Differential, TestRecommendation
from tools.safety_gate import SafetyGate

gate = SafetyGate()

print("=" * 55)
print("Phase 6 — Safety Gate Tests")
print("=" * 55)

# ── Test 1: Red flag detection ──
print("\nTest 1 — Red flag detection (sepsis in differentials)")
report1 = DiagnosticReport(
    case_id="TEST_RF",
    differentials=[
        Differential(diagnosis="Sepsis", confidence=0.6),
        Differential(diagnosis="Pneumonia", confidence=0.3),
    ],
    urgent_alerts=[],
    test_recommendations=[]
)
report1 = gate.validate(report1)
print(f"Urgent alerts : {report1.urgent_alerts}")
assert len(report1.urgent_alerts) > 0, "FAIL: No urgent alert for sepsis"
print("PASS — red flag detected")

# ── Test 2: Investigation hardening ──
print("\nTest 2 — Investigation hardening (hypothyroidism, no tests)")
report2 = DiagnosticReport(
    case_id="TEST_INV",
    differentials=[
        Differential(diagnosis="Hypothyroidism", confidence=0.9),
    ],
    urgent_alerts=[],
    test_recommendations=[]
)
report2 = gate.validate(report2)
print(f"Investigations: {[t.test_name for t in report2.test_recommendations]}")
assert len(report2.test_recommendations) >= 2, "FAIL: Investigations not injected"
print("PASS — investigations injected")

# ── Test 3: Confidence filter ──
print("\nTest 3 — Confidence filter (remove very low confidence)")
report3 = DiagnosticReport(
    case_id="TEST_CONF",
    differentials=[
        Differential(diagnosis="Hypothyroidism", confidence=0.9),
        Differential(diagnosis="PCOS",           confidence=0.05),
        Differential(diagnosis="Anaemia",        confidence=0.4),
    ],
    urgent_alerts=[],
    test_recommendations=[]
)
report3 = gate.validate(report3)
diagnoses = [d.diagnosis for d in report3.differentials]
print(f"Kept          : {diagnoses}")
assert "PCOS" not in diagnoses, "FAIL: Low confidence differential not removed"
print("PASS — low confidence differential removed")

# ── Test 4: Full pipeline + safety gate (TC001) ──
print("\nTest 4 — Full pipeline with safety gate (TC001)")
from agents.documentation_agent import DiagnosticOrchestrator

orch = DiagnosticOrchestrator()
report4 = orch.run(
    raw_input="4-month fatigue, weight gain, cold intolerance, constipation, dry skin",
    case_id="TC001_SAFE",
    age=44,
    sex="F"
)
report4 = gate.validate(report4)

print(f"Differentials : {[d.diagnosis for d in report4.differentials]}")
print(f"Investigations: {[t.test_name for t in report4.test_recommendations]}")
print(f"Urgent alerts : {report4.urgent_alerts}")
print(f"Disclaimer    : {report4.disclaimer[:60]}...")

print("\n" + "=" * 55)
print("All safety gate tests passed.")
print("=" * 55)
