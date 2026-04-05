# tools/safety_gate.py

from utils.models import DiagnosticReport, TestRecommendation

RED_FLAG_CONDITIONS = [
    "sepsis", "meningitis", "pulmonary embolism",
    "myocardial infarction", "aortic dissection",
    "subarachnoid haemorrhage", "ectopic pregnancy",
    "diabetic ketoacidosis", "stroke", "anaphylaxis",
    "appendicitis", "epiglottitis", "cardiac tamponade",
    "tension pneumothorax",
]

CONDITION_INVESTIGATIONS = {
    "hypothyroidism": [
        TestRecommendation("TSH",        "urgent",  "First-line test for hypothyroidism", "low"),
        TestRecommendation("Free T4",    "routine", "If TSH abnormal",                    "low"),
        TestRecommendation("FBC",        "routine", "Exclude anaemia",                    "low"),
    ],
    "type 2 diabetes": [
        TestRecommendation("HbA1c",      "urgent",  "Diagnostic for T2DM",               "low"),
        TestRecommendation("eGFR",       "urgent",  "Baseline renal function",            "low"),
        TestRecommendation("Urine ACR",  "routine", "Screen for nephropathy",             "low"),
    ],
    "diabetes": [
        TestRecommendation("HbA1c",          "urgent",  "Diagnostic for diabetes",       "low"),
        TestRecommendation("Fasting glucose", "urgent",  "Confirm diagnosis",             "low"),
        TestRecommendation("eGFR",            "routine", "Baseline renal function",       "low"),
    ],
    "iron deficiency anaemia": [
        TestRecommendation("FBC",          "urgent",  "Confirm anaemia and MCV",          "low"),
        TestRecommendation("Ferritin",     "urgent",  "Most sensitive for iron stores",   "low"),
        TestRecommendation("B12 + Folate", "routine", "Exclude B12/folate deficiency",    "low"),
    ],
    "anaemia": [
        TestRecommendation("FBC",        "urgent",  "Confirm anaemia",                    "low"),
        TestRecommendation("Ferritin",   "urgent",  "Iron stores",                        "low"),
        TestRecommendation("Blood film", "routine", "Morphology",                         "low"),
    ],
    "hypertension": [
        TestRecommendation("BP monitoring", "urgent",  "Confirm with ABPM",              "low"),
        TestRecommendation("eGFR",          "routine", "Renal function baseline",         "low"),
        TestRecommendation("Urine ACR",     "routine", "End-organ damage screen",         "low"),
    ],
    "depression": [
        TestRecommendation("PHQ-9", "routine", "Severity scoring",                        "low"),
        TestRecommendation("TSH",   "routine", "Exclude thyroid cause",                   "low"),
        TestRecommendation("FBC",   "routine", "Exclude organic cause",                   "low"),
    ],
    "b12 deficiency": [
        TestRecommendation("Serum B12", "urgent",  "Confirm deficiency",                  "low"),
        TestRecommendation("Folate",    "urgent",  "Often co-deficient",                  "low"),
        TestRecommendation("FBC",       "routine", "Confirm macrocytic anaemia",           "low"),
    ],
}

DISCLAIMER = (
    "This output is AI-generated clinical decision support only. "
    "It does not constitute a diagnosis. "
    "All findings must be reviewed and actioned by a qualified, "
    "registered clinician before any clinical decision is made."
)


class SafetyGate:

    def __init__(self, confidence_threshold=0.1):
        self.confidence_threshold = confidence_threshold

    def _check_red_flags(self, report):
        all_text = " ".join([
            d.diagnosis.lower() for d in report.differentials
        ] + [a.lower() for a in report.urgent_alerts])

        for condition in RED_FLAG_CONDITIONS:
            if condition in all_text:
                alert = f"URGENT: {condition.upper()} — cannot-miss diagnosis. Immediate clinical review required."
                if alert not in report.urgent_alerts:
                    report.urgent_alerts.insert(0, alert)
        return report

    def _filter_confidence(self, report):
        before = len(report.differentials)
        report.differentials = [
            d for d in report.differentials
            if d.confidence >= self.confidence_threshold
            or d.confidence == 0.0
        ]
        after = len(report.differentials)
        if before != after:
            print(f"      Safety gate removed {before - after} low-confidence differentials")
        return report

    def _harden_investigations(self, report):
        if len(report.test_recommendations) >= 3:
            return report

        for diff in report.differentials:
            diagnosis_lower = diff.diagnosis.lower()
            for condition_key, investigations in CONDITION_INVESTIGATIONS.items():
                if condition_key in diagnosis_lower:
                    existing = [t.test_name.lower() for t in report.test_recommendations]
                    for inv in investigations:
                        if inv.test_name.lower() not in existing:
                            report.test_recommendations.append(inv)
                        if len(report.test_recommendations) >= 3:
                            break
                    break
        return report

    def _inject_disclaimer(self, report):
        report.disclaimer = DISCLAIMER
        return report

    def validate(self, report):
        print("      [Safety gate] Checking red flags...")
        report = self._check_red_flags(report)
        print("      [Safety gate] Filtering confidence...")
        report = self._filter_confidence(report)
        print("      [Safety gate] Hardening investigations...")
        report = self._harden_investigations(report)
        print("      [Safety gate] Injecting disclaimer...")
        report = self._inject_disclaimer(report)
        return report
