# agents/preprocessing_agent.py

import re
import json
import os
from utils.models import Symptom, PatientCase, AuditEntry
from datetime import datetime


class PreprocessingAgent:
    """
    Agent 1 — Preprocessing & Phenotype Extraction

    Responsibilities:
    - Accept raw clinical consultation text
    - Extract symptoms using keyword matching
    - Map symptoms to HPO (Human Phenotype Ontology) codes
    - Detect negated symptoms ("no chest pain")
    - Extract duration clues ("for 3 months")
    - Return a structured PatientCase object
    """

    def __init__(self):
        self.hpo_map = self._load_hpo_map()
        self.negation_triggers = [
            "no ", "denies ", "without ", "no history of ",
            "not experiencing", "no complaint of"
        ]
        self.duration_pattern = re.compile(
            r'(\d+)\s*(day|days|week|weeks|month|months|year|years)',
            re.IGNORECASE
        )
        self.severity_keywords = {
            "mild":     ["mild", "slight", "minor", "a little"],
            "moderate": ["moderate", "moderate-severity", "noticeable"],
            "severe":   ["severe", "significant", "extreme", "debilitating"]
        }

    # ─────────────────────────────────────────
    #  HPO MAP — family medicine symptom list
    # ─────────────────────────────────────────
    def _load_hpo_map(self) -> dict:
        """
        Core symptom → HPO code mapping.
        Focused on common family medicine presentations.
        """
        return {
            # General
            "fatigue":              {"code": "HP:0012378", "term": "Fatigue"},
            "tiredness":            {"code": "HP:0012378", "term": "Fatigue"},
            "lethargy":             {"code": "HP:0001254", "term": "Lethargy"},
            "weight gain":          {"code": "HP:0004324", "term": "Weight gain"},
            "weight loss":          {"code": "HP:0001824", "term": "Weight loss"},
            "fever":                {"code": "HP:0001945", "term": "Fever"},
            "night sweats":         {"code": "HP:0030166", "term": "Night sweats"},
            "loss of appetite":     {"code": "HP:0004396", "term": "Loss of appetite"},
            "malaise":              {"code": "HP:0033834", "term": "Malaise"},

            # Endocrine / metabolic
            "cold intolerance":     {"code": "HP:0008285", "term": "Cold intolerance"},
            "heat intolerance":     {"code": "HP:0002046", "term": "Heat intolerance"},
            "excessive thirst":     {"code": "HP:0001271", "term": "Polydipsia"},
            "polydipsia":           {"code": "HP:0001271", "term": "Polydipsia"},
            "polyuria":             {"code": "HP:0000011", "term": "Polyuria"},
            "frequent urination":   {"code": "HP:0000011", "term": "Polyuria"},
            "increased urination":  {"code": "HP:0000011", "term": "Polyuria"},

            # Cardiovascular / respiratory
            "chest pain":           {"code": "HP:0100749", "term": "Chest pain"},
            "palpitations":         {"code": "HP:0001962", "term": "Palpitations"},
            "shortness of breath":  {"code": "HP:0002094", "term": "Dyspnoea"},
            "breathlessness":       {"code": "HP:0002094", "term": "Dyspnoea"},
            "dyspnoea":             {"code": "HP:0002094", "term": "Dyspnoea"},
            "cough":                {"code": "HP:0012735", "term": "Cough"},
            "wheeze":               {"code": "HP:0030828", "term": "Wheezing"},
            "wheezing":             {"code": "HP:0030828", "term": "Wheezing"},

            # Neurological
            "headache":             {"code": "HP:0002315", "term": "Headache"},
            "headaches":            {"code": "HP:0002315", "term": "Headache"},
            "dizziness":            {"code": "HP:0002321", "term": "Dizziness"},
            "lightheadedness":      {"code": "HP:0002321", "term": "Dizziness"},
            "syncope":              {"code": "HP:0001279", "term": "Syncope"},
            "tremor":               {"code": "HP:0001337", "term": "Tremor"},
            "tingling":             {"code": "HP:0000766", "term": "Paraesthesia"},
            "numbness":             {"code": "HP:0003474", "term": "Numbness"},

            # GI
            "nausea":               {"code": "HP:0002018", "term": "Nausea"},
            "vomiting":             {"code": "HP:0002013", "term": "Vomiting"},
            "constipation":         {"code": "HP:0002019", "term": "Constipation"},
            "diarrhoea":            {"code": "HP:0002014", "term": "Diarrhoea"},
            "diarrhea":             {"code": "HP:0002014", "term": "Diarrhoea"},
            "abdominal pain":       {"code": "HP:0002027", "term": "Abdominal pain"},
            "bloating":             {"code": "HP:0003270", "term": "Abdominal bloating"},
            "heartburn":            {"code": "HP:0002597", "term": "Heartburn"},

            # MSK
            "joint pain":           {"code": "HP:0002829", "term": "Joint pain"},
            "muscle weakness":      {"code": "HP:0001324", "term": "Muscle weakness"},
            "back pain":            {"code": "HP:0003418", "term": "Back pain"},
            "myalgia":              {"code": "HP:0003326", "term": "Myalgia"},

            # Skin / hair
            "hair loss":            {"code": "HP:0001596", "term": "Hair loss"},
            "dry skin":             {"code": "HP:0000958", "term": "Dry skin"},
            "rash":                 {"code": "HP:0000988", "term": "Skin rash"},
            "pallor":               {"code": "HP:0000980", "term": "Pallor"},
            "jaundice":             {"code": "HP:0000952", "term": "Jaundice"},

            # Eyes / ENT
            "blurred vision":       {"code": "HP:0000622", "term": "Blurred vision"},
            "visual loss":          {"code": "HP:0000572", "term": "Visual loss"},
            "sore throat":          {"code": "HP:0033050", "term": "Sore throat"},
            "ear pain":             {"code": "HP:0030766", "term": "Ear pain"},

            # Gynaecological
            "heavy periods":        {"code": "HP:0000132", "term": "Menorrhagia"},
            "menorrhagia":          {"code": "HP:0000132", "term": "Menorrhagia"},
            "irregular periods":    {"code": "HP:0000861", "term": "Irregular menstruation"},
            "pelvic pain":          {"code": "HP:0001901", "term": "Pelvic pain"},

            # Mental health
            "low mood":             {"code": "HP:0000716", "term": "Depression"},
            "depression":           {"code": "HP:0000716", "term": "Depression"},
            "anxiety":              {"code": "HP:0000739", "term": "Anxiety"},
            "insomnia":             {"code": "HP:0100785", "term": "Insomnia"},
            "poor sleep":           {"code": "HP:0100785", "term": "Insomnia"},
        }

    # ─────────────────────────────────────────
    #  DURATION EXTRACTION
    # ─────────────────────────────────────────
    def _extract_duration(self, text: str) -> str | None:
        match = self.duration_pattern.search(text)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        return None

    # ─────────────────────────────────────────
    #  NEGATION CHECK
    # ─────────────────────────────────────────
    def _is_negated(self, symptom: str, text: str) -> bool:
        text_lower = text.lower()
        symptom_pos = text_lower.find(symptom)
        if symptom_pos == -1:
            return False

        # only look at the current sentence — split on punctuation first
        # find the start of the sentence containing this symptom
        sentence_start = max(
            text_lower.rfind('.', 0, symptom_pos),
            text_lower.rfind(',', 0, symptom_pos),
            0
        )

        # only check within 60 chars before symptom, within same sentence
        context = text_lower[sentence_start: symptom_pos]
        return any(trigger in context for trigger in self.negation_triggers)

    # ─────────────────────────────────────────
    #  SEVERITY EXTRACTION
    # ─────────────────────────────────────────
    def _extract_severity(self, text: str) -> str | None:
        text_lower = text.lower()
        for level, keywords in self.severity_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return level
        return None

    # ─────────────────────────────────────────
    #  CORE: SYMPTOM EXTRACTION
    # ─────────────────────────────────────────
    def extract_symptoms(self, text: str) -> list[Symptom]:
        symptoms = []
        text_lower = text.lower()
        seen_codes = set()

        for keyword, hpo in self.hpo_map.items():
            if keyword in text_lower:
                # avoid duplicate HPO codes
                if hpo["code"] in seen_codes:
                    continue
                seen_codes.add(hpo["code"])

                negated  = self._is_negated(keyword, text)
                duration = self._extract_duration(text)
                severity = self._extract_severity(text)

                symptoms.append(Symptom(
                    raw_text=keyword,
                    hpo_code=hpo["code"],
                    hpo_term=hpo["term"],
                    duration=duration,
                    severity=severity,
                    is_negated=negated
                ))

        return symptoms

    # ─────────────────────────────────────────
    #  MAIN RUN METHOD
    # ─────────────────────────────────────────
    def run(
        self,
        raw_input: str,
        case_id: str,
        age: int,
        sex: str,
        pmh: list[str] = None,
        medications: list[str] = None,
        vitals: dict = None,
        social_history: str = None
    ) -> tuple[PatientCase, AuditEntry]:

        symptoms = self.extract_symptoms(raw_input)

        case = PatientCase(
            case_id=case_id,
            age=age,
            sex=sex,
            raw_input=raw_input,
            symptoms=symptoms,
            pmh=pmh or [],
            medications=medications or [],
            vitals=vitals or {},
            social_history=social_history
        )

        audit = AuditEntry(
            step="preprocessing",
            data={
                "case_id":         case_id,
                "symptoms_found":  len(symptoms),
                "symptom_terms":   [s.hpo_term for s in symptoms],
                "negated":         [s.hpo_term for s in symptoms if s.is_negated],
                "duration":        symptoms[0].duration if symptoms else None,
            },
            success=True
        )

        return case, audit