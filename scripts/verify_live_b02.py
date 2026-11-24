#!/usr/bin/env python3
"""The former split-height/carousel check is superseded by editorial layout QA."""
import runpy,sys
from pathlib import Path
sys.argv.append("--live")
runpy.run_path(str(Path(__file__).with_name("validate_editorial_composition.py")),run_name="__main__")
