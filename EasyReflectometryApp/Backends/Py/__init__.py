from . import lib_compat

lib_compat.install()  # before any Project is used; see lib_compat

from .py_backend import PyBackend  # noqa: E402

__all__ = [PyBackend]
