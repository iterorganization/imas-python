from pathlib import Path
import runpy

import pytest

courses = Path(__file__, "../../../", "docs/source/courses").resolve()
basic_course = courses / "basic"
course_snippets = []
for course in ["basic"]:
    course_snippets.extend((courses / course).glob("*snippets/*.py"))


@pytest.mark.parametrize("snippets", course_snippets)
def test_script_execution(snippets, monkeypatch):
    # Prevent showing plots in a GUI
    monkeypatch.delenv("DISPLAY", raising=False)
    runpy.run_path(str(snippets))
