from pathlib import Path
import sys

import pytest
from PySide6.QtCore import QCoreApplication


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope='session')
def qcore_application():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app