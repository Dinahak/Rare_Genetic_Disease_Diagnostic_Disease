from utils.models import (
    Symptom, PatientCase, Differential,
    TestRecommendation, AuditEntry, DiagnosticReport
)

s1 = Symptom(raw_text='fatigue', hpo_term='Fatigue', hpo_code='HP:0012378', duration='4 months')
s2 = Symptom(raw_text='weight gain', hpo_term='Weight gain', hpo_code='HP:0004324')
s3 = Symptom(raw_text='cold intolerance', hpo_term='Cold intolerance', hpo_code='HP:0008285')

case = PatientCase(
    case_id='TC001',
    age=44,
    sex='F',
    raw_input='4-month fatigue, weight gain, cold intolerance, constipation',
    symptoms=[s1, s2, s3],
    medications=[],
    pmh=[]
)

diff = Differential(
    diagnosis='Primary hypothyroidism',
    icd10_code='E03.9',
    confidence=0.87,
    supporting_symptoms=['fatigue', 'weight gain', 'cold intolerance'],
    red_flags=[]
)

test = TestRecommendation(
    test_name='TSH',
    priority='routine',
    rationale='First-line for suspected hypothyroidism'
)

report = DiagnosticReport(
    case_id='TC001',
    differentials=[diff],
    test_recommendations=[test],
    urgent_alerts=[]
)

print('case_id    :', case.case_id)
print('symptoms   :', [s.hpo_term for s in case.symptoms])
print('top diff   :', report.differentials[0].diagnosis)
print('confidence :', report.differentials[0].confidence)
print('test       :', report.test_recommendations[0].test_name)
print('generated  :', report.generated_at)
print()
print('All models working correctly.')
