import QtQuick
import QtQuick.Controls
import QtCore

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals


Item {
    id: homePage

    // Ids of the tutorials finished before (kept in tutorialSettings)
    readonly property var completedTutorials: tutorialSettings.completed.split(',').filter(Boolean)

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

        // Vertical spacer
        Item { width: 1; height: EaStyle.Sizes.fontPixelSize * 2.5 }

        // Interactive tutorials (Gui/Tutorial). Never offered by the app itself: only from here.
        EaElements.Label {
            visible: tutorials.model.length > 0
            anchors.horizontalCenter: parent.horizontalCenter
            font.bold: true
            text: qsTr('Tutorials')
        }

        EaComponents.TableView {
            id: tutorials

            visible: model.length > 0
            anchors.horizontalCenter: parent.horizontalCenter
            width: EaStyle.Sizes.fontPixelSize * 30
            showHeader: false
            tallRows: true
            maxRowCountShow: 5
            // A tutorial loads its example, which a running fit would write into.
            enabled: !Globals.BackendWrapper.analysisFittingRunning

            model: Globals.BackendWrapper.tutorialAvailable

            // Not shown, but the table takes its column widths and alignment from it.
            header: EaComponents.TableViewHeader {
                EaComponents.TableViewLabel {
                    enabled: false
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                }
                EaComponents.TableViewLabel {
                    flexibleWidth: true
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr('title / description')
                }
            }

            delegate: EaComponents.TableViewDelegate {
                readonly property var tutorial: tutorials.model[index]
                readonly property bool completed: homePage.completedTutorials.includes(tutorial.id)

                mouseArea.onPressed: Globals.References.applicationWindow.startTutorial(tutorial)

                EaComponents.TableViewLabel {
                    text: completed ? '✓' : index + 1
                    color: completed ? EaStyle.Colors.themeAccent : EaStyle.Colors.themeForegroundMinor
                    ToolTip.text: completed ? qsTr('Completed before') : ''
                }

                EaComponents.TableViewTwoRowsAdvancedLabel {
                    fontIcon: 'graduation-cap'
                    text: tutorial.title
                    minorText: qsTr('%1 (about %2 min)').arg(tutorial.summary).arg(tutorial.minutes)
                    ToolTip.text: tutorial.summary
                }
            }
        }
    }

    // The tutorials finished without a skipped step, by id, in the shared settings file.
    // The Home page is created at start-up and kept, so it hears every completion.
    Settings {
        id: tutorialSettings
        location: EaGlobals.Vars.settingsFile
        category: 'Tutorials'
        property string completed: ''
    }

    Connections {
        target: Globals.BackendWrapper.activeBackend.tutorial
        function onCompleted(id) {
            if (!homePage.completedTutorials.includes(id)) {
                tutorialSettings.completed = [...homePage.completedTutorials, id].join(',')
            }
        }
    }

    Component.onCompleted: console.debug(`Home page loaded ::: ${this}`)
    Component.onDestruction: console.debug(`Home page destroyed ::: ${this}`)

}
