import os
def test_readme_has_run_and_deploy():
    assert os.path.exists("README.md")
    t = open("README.md", encoding="utf-8").read().lower()
    assert "python build/run.py" in t
    assert "github pages" in t
