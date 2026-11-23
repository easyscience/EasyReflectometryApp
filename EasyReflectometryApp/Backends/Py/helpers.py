import os
import sys
from urllib.parse import urlparse

from PySide6.QtCore import QUrl
from PySide6.QtQml import QJSValue


def from_qml(value):
    """Unwrap a QJSValue handed over by QML (e.g. an array to a 'QVariant' slot) into plain Python data."""
    if isinstance(value, QJSValue):
        return value.toVariant()
    return value


class IO:
    @staticmethod
    def generalizePath(fpath: str) -> str:
        """
        Generalize the filepath to be platform-specific, so all file operations
        can be performed.
        :param URI rcfPath: URI to the file
        :return URI filename: platform specific URI
        """
        parsed = urlparse(fpath)
        if len(parsed.scheme) == 1:
            # A Windows drive letter (C:\...), not a URL scheme: already a local path. Parsing it
            # would drop the drive and resolve the rest against the current drive.
            return fpath
        filename = parsed.path
        if not filename or not sys.platform.startswith('win'):
            return filename
        if filename[0] == '/':
            filename = filename[1:].replace('/', os.path.sep)
        return filename

    @staticmethod
    def localFileToUrl(fpath: str) -> str:
        return QUrl.fromLocalFile(fpath).toString()

    @staticmethod
    def formatMsg(kind, *args):
        marks = {'main': '*', 'sub': '  -'}
        mark = marks[kind]
        widths = [22, 21, 20, 10]
        widths[0] -= len(mark)
        msgs = []
        for idx, arg in enumerate(args):
            # Columns past the last width are not padded.
            width = widths[idx] if idx < len(widths) else 0
            msgs.append(f'{arg:<{width}}')
        msg = ' ▌ '.join(msgs)
        msg = f'{mark} {msg}'
        return msg
