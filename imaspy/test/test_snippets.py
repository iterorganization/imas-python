from pathlib import Path
import runpy
import os

import pytest

# al4_examples = Path(__file__, '../..', 'scripts').resolve().glob('*.py')
courses = Path(__file__, "../../../", "docs/source/courses").resolve()
basic_course = courses / "basic"
basic_al4_snippets = (basic_course / "al4_snippets").glob("*.py")


@pytest.mark.skipif(
    "IMAS_HOME" not in os.environ,
    reason="IMAS_HOME must be set for tests that use the public" " IMAS database",
)  # /work/imas on SDCC
@pytest.mark.parametrize("snippets", basic_al4_snippets)
def test_script_execution(snippets):
    runpy.run_path(str(snippets))
