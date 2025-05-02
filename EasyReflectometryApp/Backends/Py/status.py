# 5SPDX-FileCopyrightText: 2025 EasyApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2025 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from .logic.parameters import Parameters as ParametersLogic
from .logic.status import Status as StatusLogic


class Status(QObject):
    statusChanged = Signal()

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._status_logic = StatusLogic(project_lib)
        self._parameters_logic = ParametersLogic(project_lib)

    @Property(str, notify=statusChanged)
    def project(self):
        return self._status_logic.project

    @Property(str, notify=statusChanged)
    def experimentsCount(self):
        return self._status_logic.experiments_count

    @Property(str, notify=statusChanged)
    def calculator(self):
        return self._status_logic.calculator

    @Property(str, notify=statusChanged)
    def minimizer(self):
        return self._status_logic.minimizer

    @Property(str, notify=statusChanged)
    def variables(self):
        return self._parameters_logic.as_status_string

    @Property(str, notify=statusChanged)
    def phaseCount(self):
        return None
