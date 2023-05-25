from pathlib import Path
import runpy
import os

import pytest

courses = Path(__file__, "../../../", "docs/source/courses").resolve()
basic_course = courses / "basic"
course_snippets = []
for course in ["basic"]:
    course_snippets.extend((courses / course).glob("*snippets/*.py"))


@pytest.mark.skipif(
    "IMAS_HOME" not in os.environ,
    reason="IMAS_HOME must be set for tests that use the public IMAS database",
)  # /work/imas on SDCC
@pytest.mark.parametrize("snippets", course_snippets)
def test_script_execution(snippets):
    runpy.run_path(str(snippets))
