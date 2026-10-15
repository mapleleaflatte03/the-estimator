from parallax.schemas import WorkItem
from parallax.estimation.engine import synthesize_forecast

wbs = [
    WorkItem(item_id="BE-1", req_ids=["REQ-1"], name="Integrate external CRM API", role="Backend",
             optimistic_hours=12, most_likely_hours=20, pessimistic_hours=40),
    WorkItem(item_id="QA-1", req_ids=["REQ-1"], name="Test integration", role="QA",
             optimistic_hours=6, most_likely_hours=10, pessimistic_hours=24),
]
result = synthesize_forecast(wbs, seed=42)
print(result.model_dump_json(indent=2))
print("\nValues are illustrative and NOT calibrated probabilities.")
