# 5SPDX-FileCopyrightText: 2025 EasyApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2025 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .helpers import IO
from .logic.summary import Summary as SummaryLogic


class Summary(QObject):
    createdChanged = Signal()
    fileNameChanged = Signal()
    summaryChanged = Signal()

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._logic = SummaryLogic(project_lib)

    @Property(bool, notify=createdChanged)
    def created(self):
        return self._logic.created

    @Property(str, notify=fileNameChanged)
    def fileName(self):
        return self._logic.file_name

    @Slot(str)
    def setFileName(self, value: str) -> None:
        self._logic.file_name = value
        self.fileNameChanged.emit()

    @Property(str, notify=fileNameChanged)
    def filePath(self) -> str:
        return str(self._logic.file_path)

    @Property(str, notify=fileNameChanged)
    def fileUrl(self) -> str:
        return IO.localFileToUrl(str(self._logic.file_path))

    @Property(str, notify=summaryChanged)
    def asHtml(self):
        return self._logic.as_html

    @Property('QVariant')
    def exportFormats(self):
        return ['HTML', 'PDF']

    @Slot()
    def saveAsHtml(self) -> None:
        self._logic.save_as_html()

    @Slot()
    def saveAsPdf(self) -> None:
        self._logic.save_as_pdf()
