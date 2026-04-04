# utils/models.py

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


# ─────────────────────────────────────────
#  1. SYMPTOM
#  Represents a single extracted symptom
# ─────────────────────────────────────────
@dataclass
class Symptom:
    raw_text: str                        # exactly as written in the note
    hpo_code: Optional[str] = None       # e.g. "HP:0012378"
    hpo_term: Optional[str] = None       # e.g. "Fatigue"
    severity: Optional[str] = None       # "mild" | "moderate" | "severe"
    duration: Optional[str] = None       # e.g. "4 months"
    is_negated: bool = False             # True if "denies chest pain"


# ─────────────────────────────────────────
#  2. PATIENT CASE
#  Everything the system knows about the patient
# ─────────────────────────────────────────
@dataclass
class PatientCase:
    case_id: str
    age: int
    sex: str                                        # "M" | "F" | "Other"
    raw_input: str                                  # original consultation note
    symptoms: List[Symptom] = field(default_factory=list)
    pmh: List[str] = field(default_factory=list)   # past medical history
    medications: List[str] = field(default_factory=list)
    social_history: Optional[str] = None
    vitals: Optional[dict] = None                  # {"hr": 88, "bp": "148/92"}
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ─────────────────────────────────────────
#  3. DIFFERENTIAL DIAGNOSIS
#  One candidate diagnosis with evidence
# ─────────────────────────────────────────
@dataclass
class Differential:
    diagnosis: str
    icd10_code: Optional[str] = None
    confidence: float = 0.0                              # 0.0 – 1.0
    supporting_symptoms: List[str] = field(default_factory=list)
    evidence_sources: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    reasoning: Optional[str] = None


# ─────────────────────────────────────────
#  4. TEST RECOMMENDATION
#  A single investigation with justification
# ─────────────────────────────────────────
@dataclass
class TestRecommendation:
    test_name: str                        # e.g. "TSH"
    priority: str = "routine"            # "urgent" | "soon" | "routine"
    rationale: Optional[str] = None      # why this test was chosen
    cost_tier: Optional[str] = None      # "low" | "medium" | "high"


# ─────────────────────────────────────────
#  5. AUDIT ENTRY
#  One logged step in the pipeline
# ─────────────────────────────────────────
@dataclass
class AuditEntry:
    step: str                            # e.g. "preprocessing" | "retrieval"
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    data: dict = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


# ─────────────────────────────────────────
#  6. DIAGNOSTIC REPORT
#  Final output returned to the physician
# ─────────────────────────────────────────
@dataclass
class DiagnosticReport:
    case_id: str
    differentials: List[Differential] = field(default_factory=list)
    urgent_alerts: List[str] = field(default_factory=list)
    test_recommendations: List[TestRecommendation] = field(default_factory=list)
    audit_trail: List[AuditEntry] = field(default_factory=list)
    disclaimer: str = (
        "This output is AI-generated decision support only. "
        "All findings must be reviewed by a qualified clinician "
        "before any clinical action is taken."
    )
    generated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )