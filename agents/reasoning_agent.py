# agents/reasoning_agent.py

from utils.models import PatientCase, AuditEntry
from tools.vector_search import VectorSearch


class ReasoningAgent:
    """
    Agent 2 — Knowledge & Retrieval

    Responsibilities:
    - Take a structured PatientCase from Agent 1
    - Build a clinical query from extracted symptoms
    - Search the vector store for relevant guidelines
    - Return top matching evidence for the LLM
    """

    def __init__(self):
        self.vector_search = VectorSearch()
        self._seed_knowledge_base()

    def _seed_knowledge_base(self):
        """
        Seeds the vector store with core family medicine
        clinical guidelines. In production this will be
        replaced by a full document indexing pipeline.
        """
        documents = [

            # ── Hypothyroidism ──
            {
                "id": "hypo_001",
                "text": "Hypothyroidism is characterised by fatigue, weight gain, cold intolerance, constipation, dry skin, hair thinning, and low mood. TSH is elevated and Free T4 is low. First-line treatment is levothyroxine.",
                "metadata": {"condition": "Hypothyroidism", "source": "NICE CKS", "type": "guideline"}
            },
            {
                "id": "hypo_002",
                "text": "Primary hypothyroidism investigations: TSH (first line), Free T4 if TSH abnormal, FBC to exclude anaemia, lipid profile as dyslipidaemia is common. Thyroid peroxidase antibodies if autoimmune cause suspected.",
                "metadata": {"condition": "Hypothyroidism", "source": "NICE CKS", "type": "investigations"}
            },
            {
                "id": "hypo_003",
                "text": "Subclinical hypothyroidism: TSH elevated but Free T4 normal. Monitor 6-monthly. Treat if TSH above 10, symptomatic, or planning pregnancy. Common in women over 40.",
                "metadata": {"condition": "Hypothyroidism", "source": "NICE CKS", "type": "guideline"}
            },

            # ── Type 2 Diabetes ──
            {
                "id": "dm2_001",
                "text": "Type 2 diabetes presents with polydipsia, polyuria, blurred vision, weight loss, fatigue, and recurrent infections. Risk factors: obesity, family history, South Asian ethnicity, age over 45.",
                "metadata": {"condition": "Type 2 Diabetes", "source": "NICE NG28", "type": "guideline"}
            },
            {
                "id": "dm2_002",
                "text": "Diabetes diagnosis criteria: fasting plasma glucose 7.0 mmol/L or above, random glucose 11.1 mmol/L or above, HbA1c 48 mmol/mol or above. Requires two abnormal results if asymptomatic.",
                "metadata": {"condition": "Type 2 Diabetes", "source": "NICE NG28", "type": "diagnosis"}
            },
            {
                "id": "dm2_003",
                "text": "Type 2 diabetes investigations: HbA1c, fasting glucose, eGFR, urine ACR for nephropathy, lipid profile, foot examination, retinal screening referral, blood pressure monitoring.",
                "metadata": {"condition": "Type 2 Diabetes", "source": "NICE NG28", "type": "investigations"}
            },
            {
                "id": "dm2_004",
                "text": "Peripheral neuropathy in diabetes: tingling, numbness, burning in feet and hands. Assess with 10g monofilament test and vibration sense. Annual foot review recommended.",
                "metadata": {"condition": "Diabetic Neuropathy", "source": "NICE NG28", "type": "complication"}
            },

            # ── Iron Deficiency Anaemia ──
            {
                "id": "ida_001",
                "text": "Iron deficiency anaemia presents with fatigue, pallor, shortness of breath on exertion, palpitations, headache, and koilonychia. Common causes: menorrhagia, poor dietary intake, GI blood loss.",
                "metadata": {"condition": "Iron Deficiency Anaemia", "source": "NICE CKS", "type": "guideline"}
            },
            {
                "id": "ida_002",
                "text": "Iron deficiency anaemia investigations: FBC (low Hb, low MCV), serum ferritin (most sensitive), iron studies, reticulocyte count. In women with menorrhagia, pelvic ultrasound to exclude fibroids.",
                "metadata": {"condition": "Iron Deficiency Anaemia", "source": "NICE CKS", "type": "investigations"}
            },
            {
                "id": "ida_003",
                "text": "Vitamin B12 deficiency causes megaloblastic anaemia, fatigue, peripheral neuropathy, and glossitis. At risk: vegans, vegetarians, elderly, those on metformin. Check serum B12 and folate.",
                "metadata": {"condition": "B12 Deficiency", "source": "NICE CKS", "type": "guideline"}
            },

            # ── Hypertension ──
            {
                "id": "htn_001",
                "text": "Hypertension diagnosis requires clinic BP above 140/90 confirmed by ABPM or home monitoring. Stage 1: 135/85 to 149/94. Stage 2: 150/95 or above. Offer treatment at stage 1 if under 80 with end-organ damage or 10-year cardiovascular risk above 10 percent.",
                "metadata": {"condition": "Hypertension", "source": "NICE NG136", "type": "guideline"}
            },
            {
                "id": "htn_002",
                "text": "Hypertension investigations: urine ACR, eGFR, HbA1c, lipid profile, 12-lead ECG. Assess for secondary causes if resistant or early onset. Calculate QRISK3 for cardiovascular risk.",
                "metadata": {"condition": "Hypertension", "source": "NICE NG136", "type": "investigations"}
            },

            # ── Red Flag conditions ──
            {
                "id": "rf_001",
                "text": "Sepsis red flags: temperature above 38.3 or below 36, HR above 90, RR above 20, altered mental status, systolic BP below 90. Immediate hospital referral required. Do not delay antibiotics.",
                "metadata": {"condition": "Sepsis", "source": "NICE NG51", "type": "red_flag"}
            },
            {
                "id": "rf_002",
                "text": "Pulmonary embolism red flags: sudden dyspnoea, pleuritic chest pain, haemoptysis, tachycardia. Wells score guides investigation. D-dimer and CTPA. High clinical suspicion warrants immediate referral.",
                "metadata": {"condition": "Pulmonary Embolism", "source": "NICE NG158", "type": "red_flag"}
            },
            {
                "id": "rf_003",
                "text": "Myocardial infarction: central crushing chest pain, radiation to jaw or arm, diaphoresis, nausea. Call 999 immediately. Aspirin 300mg if not contraindicated. ECG on arrival.",
                "metadata": {"condition": "Myocardial Infarction", "source": "NICE NG185", "type": "red_flag"}
            },

            # ── Mental Health ──
            {
                "id": "mh_001",
                "text": "Depression in primary care: persistent low mood, anhedonia, fatigue, sleep disturbance, poor concentration, feelings of worthlessness. PHQ-9 for severity. Offer CBT or antidepressants for moderate to severe.",
                "metadata": {"condition": "Depression", "source": "NICE CG90", "type": "guideline"}
            },
            {
                "id": "mh_002",
                "text": "Anxiety disorders: generalised anxiety, panic disorder, social anxiety. GAD-7 for screening. First line: CBT and SSRIs. Rule out thyroid disease, arrhythmia, and substance misuse as organic causes.",
                "metadata": {"condition": "Anxiety", "source": "NICE CG113", "type": "guideline"}
            },
        ]

        self.vector_search.index_documents(documents)

    def _build_query(self, case: PatientCase) -> str:
        """
        Build a search query from the patient case.
        Weights active symptoms more heavily than history.
        """
        parts = []

        # active symptoms only — negated ones excluded
        active_symptoms = [
            s.hpo_term for s in case.symptoms
            if s.hpo_term and not s.is_negated
        ]
        if active_symptoms:
            # repeat symptoms to weight them higher in vector search
            parts.append(", ".join(active_symptoms))
            parts.append(", ".join(active_symptoms))

        if case.pmh:
            parts.append("History: " + ", ".join(case.pmh))

        if case.medications:
            parts.append("Medications: " + ", ".join(case.medications))

        parts.append(f"{case.age}yo {case.sex}")

        return ". ".join(parts)

    def run(self, case: PatientCase, top_k: int = 5) -> tuple[list[dict], AuditEntry]:
        """
        Main entry point. Takes a PatientCase,
        retrieves relevant clinical documents,
        returns them with an audit entry.
        """
        query = self._build_query(case)
        results = self.vector_search.retrieve(query, top_k=top_k)

        audit = AuditEntry(
            step="retrieval",
            data={
                "case_id":        case.case_id,
                "query":          query,
                "docs_retrieved": len(results),
                "top_conditions": [
                    r["metadata"].get("condition", "unknown")
                    for r in results
                ]
            },
            success=True
        )

        return results, audit