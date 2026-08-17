// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals
import "./Groups" as Groups


EaComponents.SideBarColumn {

    Groups.PlotControl {}

    Groups.PolarizationChannels {
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }

}
