// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import "./Groups" as Groups


EaComponents.SideBarColumn {

//    Groups.ParamNames {}

    Groups.Calculator {}

    Groups.Minimizer {}
}
