import QtQuick

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


Item {

    Column {
        anchors.centerIn: parent

        // Application logo
        Image {
            id: appLogo

            source: Globals.ApplicationInfo.about.icon
            anchors.horizontalCenter: parent.horizontalCenter
            width: EaStyle.Sizes.fontPixelSize * 5
            fillMode: Image.PreserveAspectFit
            antialiasing: true
        }
        // Application logo

        // Application name
        Row {
            id: appName

            property string fontFamily: EaStyle.Fonts.thirdFontFamily
            property string fontPixelSize: EaStyle.Sizes.fontPixelSize * 4

            anchors.horizontalCenter: parent.horizontalCenter

            EaElements.Label {
                font.family: parent.fontFamily
                font.pixelSize: parent.fontPixelSize
                font.weight: Font.Light
                text: Globals.ApplicationInfo.about.namePrefixForLogo
            }
            EaElements.Label {
                font.family: parent.fontFamily
                font.pixelSize: parent.fontPixelSize
                font.weight: Font.DemiBold
                text: Globals.ApplicationInfo.about.nameSuffixForLogo
            }
        }
        // Application name

        // Application version
        EaElements.Label {
            id: appVersion

            anchors.horizontalCenter: parent.horizontalCenter

            text: {
                return qsTr('Version') + ` ${Globals.BackendWrapper.homeVersionNumber} (${Globals.BackendWrapper.homeVersionDate})`
            }
        }
        // Application version

        // Vertical spacer
        Item { width: 1; height: EaStyle.Sizes.fontPixelSize * 2.5 }

        // Start button
        EaElements.SideBarButton {
            id: startButton

            anchors.horizontalCenter: parent.horizontalCenter

            fontIcon: 'rocket'
            text: qsTr('Start')
            onClicked: {
                console.debug(`Clicking '${text}' button ::: ${this}`)
                Globals.References.applicationWindow.appBarCentralTabs.projectButton.enabled = true
                Globals.References.applicationWindow.appBarCentralTabs.projectButton.toggle()
            }
        }

        // Vertical spacer
        Item { width: 1; height: EaStyle.Sizes.fontPixelSize * 2.5 }

        // Links
        Row {
            id: links

            anchors.horizontalCenter: parent.horizontalCenter
            spacing: EaStyle.Sizes.fontPixelSize * 3

            // Left links
            Column {
                spacing: EaStyle.Sizes.fontPixelSize

                EaElements.Button {
                    text: qsTr('About %1'.arg(Globals.ApplicationInfo.about.name))
                    onClicked: EaGlobals.Vars.showAppAboutDialog = true
                    Loader { source: 'Popups/About.qml' }
                }
            }
            // Left links

            // Right links
            Column {
                spacing: EaStyle.Sizes.fontPixelSize

                EaElements.Button {
                    text: qsTr('Online documentation')
                    onClicked: Qt.openUrlExternally(Globals.BackendWrapper.homeUrlsDocumentation)
                }
            }
            // Right links
        }
        // Links
    }

    Component.onCompleted: console.debug(`Home page loaded ::: ${this}`)
    Component.onDestruction: console.debug(`Home page destroyed ::: ${this}`)

}
