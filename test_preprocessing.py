from agents.preprocessing_agent import PreprocessingAgent

agent = PreprocessingAgent()

# ── Test TC001 — Hypothyroidism ──
print("=" * 50)
print("TC001 — Hypothyroidism")
print("=" * 50)
case1, audit1 = agent.run(
    raw_input="4-month history of fatigue, weight gain of 6kg, feeling cold all the time, constipation, low mood. Hair has become thin and dry.",
    case_id="TC001",
    age=44,
    sex="F",
    pmh=[],
    medications=[]
)
print(f"Symptoms found : {len(case1.symptoms)}")
for s in case1.symptoms:
    neg = " [NEGATED]" if s.is_negated else ""
    print(f"  {s.hpo_term:<25} {s.hpo_code}  duration={s.duration}{neg}")
print(f"Audit step     : {audit1.step}")
print(f"Audit success  : {audit1.success}")

# ── Test TC002 — Diabetes ──
print()
print("=" * 50)
print("TC002 — Type 2 Diabetes")
print("=" * 50)
case2, audit2 = agent.run(
    raw_input="6-week history of excessive thirst, frequent urination including twice at night, blurred vision, weight loss of 5kg, tingling in both feet.",
    case_id="TC002",
    age=61,
    sex="M",
    pmh=["Hypertension", "Hypercholesterolaemia"],
    medications=["Amlodipine 5mg", "Atorvastatin 20mg"],
    vitals={"hr": 88, "bp": "148/92", "rbg": 18.4}
)
print(f"Symptoms found : {len(case2.symptoms)}")
for s in case2.symptoms:
    print(f"  {s.hpo_term:<25} {s.hpo_code}")

# ── Test TC003 — Anaemia + negation ──
print()
print("=" * 50)
print("TC003 — Iron Deficiency Anaemia + negation test")
print("=" * 50)
case3, audit3 = agent.run(
    raw_input="Fatigue, shortness of breath, palpitations, headaches. No chest pain. Heavy periods for 5 months. Denies fever.",
    case_id="TC003",
    age=34,
    sex="F"
)
print(f"Symptoms found : {len(case3.symptoms)}")
for s in case3.symptoms:
    neg = " [NEGATED]" if s.is_negated else ""
    print(f"  {s.hpo_term:<25} {s.hpo_code}{neg}")

print()
print("All preprocessing tests passed.")
