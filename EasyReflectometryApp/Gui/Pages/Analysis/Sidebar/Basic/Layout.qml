// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import EasyApp.Gui.Style 1.0 as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import "./Groups" as Groups
import Gui.Globals as Globals


EaComponents.SideBarColumn {

    Groups.Experiments{}
//        enabled: Globals.BackendWrapper.analysisIsFitFinished
//    }

//    EaElements.GroupBox {
//        collapsible: false
//        last: true
//
//        Loader { source: 'Experiments.qml' }
//    }

    Groups.Fittables{}

/*    EaElements.GroupBox {
        //title: qsTr("Parameters")
        collapsible: false
        last: true

        Loader { source: 'Fittables.qml' }
    }
*/
    Groups.Fitting{}

/*    EaElements.GroupBox {
        //title: qsTr("Fitting")
        collapsible: false

        Loader { source: 'Fitting.qml' }
    }
*/
}
