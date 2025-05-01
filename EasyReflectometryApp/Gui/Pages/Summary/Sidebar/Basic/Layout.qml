// 5SPDX-FileCopyrightText: 2025 EasyApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import QtQuick

import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals


EaComponents.SideBarColumn {

    EaElements.GroupBox {
        enabled: Globals.BackendWrapper.summaryCreated
        title: qsTr('Export summary')
        icon: 'download'
        collapsed: false

        Loader { source: 'Groups/Export.qml' }
    }

}
