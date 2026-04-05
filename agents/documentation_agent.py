# agents/documentation_agent.py

import os
import json
from datetime import datetime
from utils.models import (
    PatientCase, DiagnosticReport,
    Differential, TestRecommendation, AuditEntry
)
from agents.preprocessing_agent import PreprocessingAgent
from agents.reasoning_agent import ReasoningAgent
from models.llm_loader import LLMClient
from config.settings import FM_SYSTEM_PROMPT


class DiagnosticOrchestrator:
    """
    Agent 3 — Diagnostic Orchestrator

    Responsibilities:
    - Coordinate the full pipeline: Agent 1 → Agent 2 → LLM
    - Run a self-critique pass on the initial response
    - Parse LLM output into structured DiagnosticReport
    - Write audit log for every run
    - Return a complete DiagnosticReport
    """

    def __init__(self):
        self.preprocessor = PreprocessingAgent()
        self.retriever    = ReasoningAgent()
        self.llm          = LLMClient()
        self.audit_dir    = os.getenv("AUDIT_LOG_DIR", "./data/audit_logs")
        os.makedirs(self.audit_dir, exist_ok=True)

    # ─────────────────────────────────────────
    #  BUILD CLINICAL PROMPT
    # ─────────────────────────────────────────
    def _build_prompt(self, case: PatientCase, docs: list[dict]) -> str:
        symptom_list = ", ".join([
            s.hpo_term for s in case.symptoms
            if s.hpo_term and not s.is_negated
        ])

        top_condition = docs[0]['metadata'].get('condition', '') if docs else ''
        top_evidence  = docs[0]['text'][:150] if docs else ''

        prompt = f"""Patient: {case.age}yo {case.sex}
Symptoms: {symptom_list}
Top evidence: {top_condition} — {top_evidence}

Give 2 diagnoses with confidence % and 2 investigations."""

        return prompt

    # ─────────────────────────────────────────
    #  PARSE LLM RESPONSE
    # ─────────────────────────────────────────
    def _parse_response(self, response: str, case_id: str) -> DiagnosticReport:
        """
        Parse raw LLM text into a structured DiagnosticReport.
        Handles the Qwen output format:
            Diagnosis 1: [name]
            Confidence Percentage: 90%
            Investigation 1: [name]
        """
        lines         = response.strip().split("\n")
        differentials = []
        tests         = []
        urgent_alerts = []

        current_diagnosis    = None
        current_confidence   = 0.0
        current_investigation = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line_lower = line.lower()

            # ── Diagnosis lines ──
            if line_lower.startswith("diagnosis"):
                # save previous diagnosis if exists
                if current_diagnosis:
                    differentials.append(Differential(
                        diagnosis=current_diagnosis,
                        confidence=current_confidence,
                        supporting_symptoms=[],
                        red_flags=[]
                    ))
                # start new diagnosis — extract name after colon
                parts = line.split(":", 1)
                current_diagnosis  = parts[1].strip() if len(parts) > 1 else line
                current_confidence = 0.0

            # ── Confidence lines ──
            elif "confidence" in line_lower and "%" in line:
                try:
                    pct = [
                        w.strip().replace("%", "").replace(",", "")
                        for w in line.split()
                        if "%" in w
                    ]
                    if pct:
                        current_confidence = float(pct[0]) / 100
                except ValueError:
                    current_confidence = 0.0

            # ── Investigation lines ──
            elif line_lower.startswith("investigation"):
                # save previous diagnosis before starting investigations
                if current_diagnosis:
                    differentials.append(Differential(
                        diagnosis=current_diagnosis,
                        confidence=current_confidence,
                        supporting_symptoms=[],
                        red_flags=[]
                    ))
                    current_diagnosis = None

                parts = line.split(":", 1)
                current_investigation = parts[1].strip() if len(parts) > 1 else line

                # only add unique investigations
                existing = [t.test_name for t in tests]
                if current_investigation not in existing:
                    tests.append(TestRecommendation(
                        test_name=current_investigation,
                        priority="routine",
                        rationale="Recommended based on clinical presentation"
                    ))

            # ── Urgent / red flag lines ──
            if any(term in line_lower for term in [
                "urgent", "cannot-miss", "emergency",
                "immediate", "red flag", "999", "refer now"
            ]):
                urgent_alerts.append(line)

        # save last diagnosis if not yet saved
        if current_diagnosis:
            differentials.append(Differential(
                diagnosis=current_diagnosis,
                confidence=current_confidence,
                supporting_symptoms=[],
                red_flags=[]
            ))

        return DiagnosticReport(
            case_id=case_id,
            differentials=differentials[:5],
            urgent_alerts=urgent_alerts,
            test_recommendations=tests[:3],
            audit_trail=[]
        )

    # ─────────────────────────────────────────
    #  SELF CRITIQUE
    # ─────────────────────────────────────────
    def _self_critique(self, initial_response: str, case: PatientCase) -> str:
        symptom_list = ", ".join([
            s.hpo_term for s in case.symptoms
            if not s.is_negated
        ])[:100]

        critique_prompt = f"""Patient {case.age}yo {case.sex}, symptoms: {symptom_list}
Diagnosis given: {initial_response[:150]}
Any missed red flags? One sentence only."""

        return self.llm.generate(
            "You are a senior GP. Be very brief.",
            critique_prompt
        )

    # ─────────────────────────────────────────
    #  SAVE AUDIT LOG
    # ─────────────────────────────────────────
    def _save_audit(self, case_id: str, audit_entries: list[AuditEntry]):
        path = os.path.join(self.audit_dir, f"{case_id}.json")
        data = {
            "case_id":   case_id,
            "timestamp": datetime.utcnow().isoformat(),
            "steps":     [
                {
                    "step":    e.step,
                    "time":    e.timestamp,
                    "success": e.success,
                    "data":    e.data
                }
                for e in audit_entries
            ]
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Audit saved → {path}")

    # ─────────────────────────────────────────
    #  MAIN RUN METHOD
    # ─────────────────────────────────────────
    def run(
        self,
        raw_input:     str,
        case_id:       str,
        age:           int,
        sex:           str,
        pmh:           list[str] = None,
        medications:   list[str] = None,
        vitals:        dict      = None,
        social_history: str      = None
    ) -> DiagnosticReport:

        audit_trail = []

        # ── Step 1: Preprocess ──
        print(f"\n[1/4] Preprocessing case {case_id}...")
        case, audit_pre = self.preprocessor.run(
            raw_input, case_id, age, sex,
            pmh=pmh, medications=medications,
            vitals=vitals, social_history=social_history
        )
        audit_trail.append(audit_pre)
        print(f"      Symptoms found: {len(case.symptoms)}")

        # ── Step 2: Retrieve ──
        print(f"[2/4] Retrieving evidence...")
        docs, audit_rag = self.retriever.run(case, top_k=3)
        audit_trail.append(audit_rag)
        print(f"      Documents retrieved: {len(docs)}")

        # ── Step 3: LLM Reasoning ──
        print(f"[3/4] Running LLM reasoning...")
        prompt = self._build_prompt(case, docs)
        initial_response = self.llm.generate(FM_SYSTEM_PROMPT, prompt)

        audit_trail.append(AuditEntry(
            step="llm_reasoning",
            data={
                "case_id":         case_id,
                "response_length": len(initial_response),
                "model":           self.llm.model
            },
            success=not initial_response.startswith("ERROR")
        ))
        print(f"      LLM response received ({len(initial_response)} chars)")
        
        # ── Step 4: Self Critique ──
        print(f"[4/4] Running self-critique...")
        critique = self._self_critique(initial_response, case)

        audit_trail.append(AuditEntry(
            step="self_critique",
            data={
                "case_id":  case_id,
                "critique": critique[:200]
            },
            success=not critique.startswith("ERROR")
        ))
        print(f"      Critique complete")

        # ── Parse into report ──
        report = self._parse_response(initial_response, case_id)
        report.audit_trail = audit_trail

        # ── Save audit log ──
        self._save_audit(case_id, audit_trail)

        return report