# 5SPDX-FileCopyrightText: 2026 EasyApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

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
    plotFileNameChanged = Signal()
    htmlExportingFinished = Signal(bool, str)

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

    @Property(str, notify=plotFileNameChanged)
    def plotFileName(self):
        return self._logic.plot_file_name

    @Slot(str)
    def setPlotFileName(self, value: str) -> None:
        self._logic.plot_file_name = value
        self.plotFileNameChanged.emit()

    @Property(str, notify=plotFileNameChanged)
    def plotFilePath(self) -> str:
        return str(self._logic.plot_file_path)

    @Property(str, notify=plotFileNameChanged)
    def plotFileUrl(self) -> str:
        return IO.localFileToUrl(str(self._logic.plot_file_path))

    @Property('QVariant', notify=plotFileNameChanged)
    def plotExportFormats(self):
        return ['PDF', 'PNG', 'SVG']

    @Property(str, notify=summaryChanged)
    def asHtml(self):
        return self._logic.as_html

    @Property('QVariant', notify=summaryChanged)
    def exportFormats(self):
        return ['HTML', 'PDF']

    @Slot(str)
    def saveAsHtml(self, path: str = '') -> None:
        try:
            self._logic.save_as_html(path or None)
            target = path or str(self._logic.file_path.with_suffix('.html'))
            self.htmlExportingFinished.emit(True, target)
        except Exception:  # noqa: BLE001
            self.htmlExportingFinished.emit(False, path)

    @Slot(str)
    def saveAsPdf(self, path: str = '') -> None:
        try:
            self._logic.save_as_pdf(path or None)
            target = path or str(self._logic.file_path.with_suffix('.pdf'))
            self.htmlExportingFinished.emit(True, target)
        except Exception:  # noqa: BLE001
            self.htmlExportingFinished.emit(False, path)

    @Slot(str, float, float)
    def savePlot(self, path: str, width_cm: float, height_cm: float) -> None:
        try:
            self._logic.save_plot(path, width_cm, height_cm)
            self.htmlExportingFinished.emit(True, path)
        except Exception:  # noqa: BLE001
            self.htmlExportingFinished.emit(False, path)

    @Slot(float, float)
    def showPlot(self, width_cm: float, height_cm: float) -> None:
        self._logic.show_plot(width_cm, height_cm)
