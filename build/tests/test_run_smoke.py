# build/tests/test_run_smoke.py
import os
from build.run import run

def test_run_produces_data_and_report():
    summary = run(refresh=False)
    assert summary["products"] > 40       # all docx products across 5 categories
    assert os.path.exists("catalogue-data.js")
    assert os.path.exists("build-report.txt")
    # Rakhi/Bathrobes are docx-only → some unmatched is expected and fine.
    assert isinstance(summary["unmatched"], list)
    assert len(summary["unmatched"]) > 0   # Rakhi + Bathrobes are always docx-only
