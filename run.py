# SPDX-FileCopyrightText: 2026 EasyReflectometryApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyReflectometryApp project <https://github.com/easyscience/EasyReflectometryApp>
"""Run the application from a source checkout: `python run.py [main.py options]`."""

import runpy
import sys
from pathlib import Path

MAIN = Path(__file__).resolve().parent / 'EasyReflectometryApp' / 'main.py'

# main.py imports `Backends.Py` relative to its own folder, as when it is run directly.
sys.path.insert(0, str(MAIN.parent))
sys.argv[0] = str(MAIN)
runpy.run_path(str(MAIN), run_name='__main__')
