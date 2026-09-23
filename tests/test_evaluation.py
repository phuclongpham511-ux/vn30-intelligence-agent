import json
from pathlib import Path


def test_materiality_examples_capture_personalization():
    cases = json.loads((Path(__file__).parents[1] / "evaluation/materiality_cases.json").read_text())
    assert len(cases) >= 2
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert cases[0]["event"] == cases[1]["event"]
    assert cases[0]["expected_level"] != cases[1]["expected_level"]
