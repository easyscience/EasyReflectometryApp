// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Parameter names")
    icon: "paint-brush"
    collapsed: false
    EaElements.GroupRow{

        EaComponents.TableView {
            id: tableView

            readonly property var param: {
                "blockType": "model",
                "blockIcon": "layer-group",
                "blockIdx": 0,
                "blockName": "co2sio4",
                "categoryIcon": "atom",
                "category": "_atom_site",
                "prettyCategory": "atom",
                "rowIndex": 2,
                "rowName": "Si",
                "icon": "map-marker-alt",
                "name": "_fract_x",
                "prettyName": "fract x",
                "shortPrettyName": "x" }

            showHeader: false
            tallRows: true
            maxRowCountShow: model.length

            /*
            model: [
                { value: EaGlobals.Vars.ShortestWithIconsAndPrettyLabels,
                    text: qsTr('Shortest iconified name with pretty labels') },
                { value: EaGlobals.Vars.ReducedWithIconsAndPrettyLabels,
                    text: qsTr('Shorter iconified name with pretty labels') },
                { value: EaGlobals.Vars.FullWithIconsAndPrettyLabels,
                    text: qsTr('Full iconified name with pretty labels') },
                { value: EaGlobals.Vars.FullWithPrettyLabels,
                    text: qsTr('Full plain text name with pretty labels') },
                { value: EaGlobals.Vars.FullWithLabels,
                    text: qsTr('Full plain text name with labels') },
                { value: EaGlobals.Vars.FullWithIndices,
                    text: qsTr('Full plain text name with indices') }
            ]
            */

            model: [
                { value: EaGlobals.Vars.ShortestWithIconsAndPrettyLabels,
                    text: qsTr('Iconified name with pretty labels') },
                { value: EaGlobals.Vars.PlainShortWithLabels,
                    text: qsTr('Short plain text name with labels') },
                { value: EaGlobals.Vars.PlainFullWithLabels,
                    text: qsTr('Full plain text name with labels') }
            ]

            header: EaComponents.TableViewHeader {

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                }

                EaComponents.TableViewLabel {
                    flexibleWidth: true
                }
            }

            delegate: EaComponents.TableViewDelegate {
                mouseArea.onPressed: EaGlobals.Vars.paramNameFormat = currentIndex

                EaElements.RadioButton {
                    checked: index === EaGlobals.Vars.paramNameFormat
                    anchors.verticalCenter: parent.verticalCenter
                }

                EaComponents.TableViewTwoRowsAdvancedLabel {
                    text: tableView.model[index].text
                    minorText: Globals.Proxies.paramName(param, tableView.model[index].value)
                }
            }
        }
    }
}
