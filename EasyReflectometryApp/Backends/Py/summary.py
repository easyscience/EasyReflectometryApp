# 5SPDX-FileCopyrightText: 2026 EasyApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import logging
from html import escape

from EasyApplication.Logic.Logging import console
from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .helpers import IO
from .logic.summary import Summary as SummaryLogic

logger = logging.getLogger(__name__)


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
        return ['PDF', 'PNG', 'SVG', 'PICKLE']

    @Property(str, notify=summaryChanged)
    def asHtml(self):
        # QML reads this property, so an exception here escapes into Qt's C++
        # signal delivery and aborts the process with no traceback (an access
        # violation on Windows). Report the failure in the report itself
        # instead: a broken summary must not take the application down.
        try:
            return self._logic.as_html
        except Exception as exception:  # noqa: BLE001 - never let the report kill the app
            console.error(f'Failed to compile the HTML summary: {exception}')
            logger.exception('Failed to compile the HTML summary')
            return f'<html><body><h3>The summary could not be generated</h3><p>{escape(str(exception))}</p></body></html>'

    @Property('QVariant', notify=summaryChanged)
    def exportFormats(self):
        return ['HTML', 'PDF']

    @Slot()
    def refreshPaths(self) -> None:
        """Re-emit path-related signals so QML bindings re-evaluate.

        Call this whenever the project path changes so that filePath,
        fileUrl, plotFilePath and plotFileUrl stay in sync.
        """
        self.fileNameChanged.emit()
        self.plotFileNameChanged.emit()

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
