"""
What main.py needs before the scientific stack is imported. Keep this package free of
heavy imports (numpy, easyscience, Backends, ...): it is what puts the splash on screen
while those load. tests/test_startup.py guards it.
"""

from .application import Application
from .application import Rendering
from .splash import Splash

__all__ = ['Application', 'Rendering', 'Splash']
