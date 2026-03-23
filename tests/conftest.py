import pytest
from PySide6.QtCore import QCoreApplication


@pytest.fixture(scope='session')
def qcore_application():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app
    app.quit()
