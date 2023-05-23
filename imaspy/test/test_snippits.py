from pathlib import Path
import runpy
import os

import pytest

# al4_examples = Path(__file__, '../..', 'scripts').resolve().glob('*.py')
courses = Path(__file__, "../../../", "docs/source/courses").resolve()
basic_course = courses / "basic"
basic_al4_snippits = (basic_course / "al4_snippits").glob("*.py")


@pytest.mark.skipif(
    "IMAS_HOME" not in os.environ,
    reason="IMAS_HOME must be set for tests that use the public" " IMAS database",
)  # /work/imas on SDCC
@pytest.mark.parametrize("snippits", basic_al4_snippits)
def test_script_execution(snippits):
    runpy.run_path(str(snippits))
