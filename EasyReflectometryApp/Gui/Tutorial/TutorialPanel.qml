// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

import "Targets.js" as Targets


// The interactive tutorial panel, docked on the left of the pages, with the frame around the
// current step's control (MD/INTERACTIVE_TUTORIALS_DESIGN.md, sections 2 and 5.7). Plain
// rectangles and text only: no Popup, layer, shader or opacity animation, which have failed in
// software rendering before.
Rectangle {
    id: panel

    // Where the controls are searched for: the window's content item.
    required property Item targetRoot
    // Starts the tutorial again from its example (ApplicationWindow.startTutorial).
    required property var restart
    property real windowWidth: 0

    readonly property var backend: Globals.BackendWrapper
    readonly property var step: backend.tutorialStep
    readonly property bool active: backend.tutorialState !== 'idle'
    readonly property string currentPage: Targets.PAGES[EaGlobals.Vars.appBarCurrentIndex] ?? ''

    property bool collapsed: false
    readonly property real fullWidth: EaStyle.Sizes.fontPixelSize * 20
    readonly property real stripWidth: EaStyle.Sizes.fontPixelSize * 2.5
    // The charts keep at least 480 px beside the docked panel; in a narrower window the
    // expanded panel lies over them instead of pushing them aside.
    readonly property bool fits: windowWidth - EaStyle.Sizes.sideBarWidth - fullWidth >= 480
    // What the pages give up (ApplicationWindow binds the content area's left margin to it).
    readonly property real dockedWidth: !active ? 0 : (collapsed || !fits ? stripWidth : fullWidth)

    // What is framed, and why it is not the step's control (also read by tests/tutorial_run_harness.py)
    readonly property Item frameItem: frame.item
    readonly property string frameNote: frame.note
    readonly property bool showMeEnabled: active && (step.hasCondition ?? false) && !showingMe && step.state !== 'done'
                                          && !backend.analysisFittingRunning
                                          // Do not type over what the user is typing.
                                          && !(Window.activeFocusItem && Window.activeFocusItem.hasOwnProperty('cursorPosition'))

    // Called when a tutorial starts.
    function opened() {
        collapsed = !fits
        showMeError = ''
    }

    visible: active
    width: !active ? 0 : (collapsed ? stripWidth : fullWidth)
    color: EaStyle.Colors.contentBackground

    Rectangle {
        anchors.right: parent.right
        width: 1
        height: parent.height
        color: EaStyle.Colors.appBorder
    }

    ///////////////////////
    // Collapsed: the strip
    ///////////////////////
    Column {
        visible: panel.collapsed
        anchors.horizontalCenter: parent.horizontalCenter
        y: EaStyle.Sizes.fontPixelSize * 0.5
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        EaElements.ToolButton {
            fontIcon: 'angle-double-right'
            ToolTip.text: qsTr('Show the tutorial')
            onClicked: panel.collapsed = false
        }
        EaElements.Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: `${panel.backend.tutorialStepIndex + 1}/${panel.backend.tutorialStepCount}`
        }
    }

    ///////////////////////
    // Expanded
    ///////////////////////
    Flickable {
        visible: !panel.collapsed
        anchors.fill: parent
        anchors.margins: EaStyle.Sizes.fontPixelSize
        contentHeight: content.height
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        Column {
            id: content
            width: parent.width
            spacing: EaStyle.Sizes.fontPixelSize * 0.75

            // Title and collapse
            Item {
                width: parent.width
                height: Math.max(titleLabel.height, collapseButton.height)

                EaElements.Label {
                    id: titleLabel
                    anchors.left: parent.left
                    anchors.right: collapseButton.left
                    anchors.verticalCenter: parent.verticalCenter
                    wrapMode: Text.WordWrap
                    font.bold: true
                    font.pixelSize: EaStyle.Sizes.fontPixelSize * 1.2
                    text: panel.backend.tutorialTitle
                }
                EaElements.ToolButton {
                    id: collapseButton
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    fontIcon: 'angle-double-left'
                    ToolTip.text: qsTr('Collapse the tutorial')
                    onClicked: panel.collapsed = true
                }
            }

            // Progress
            EaElements.Label {
                visible: panel.backend.tutorialState === 'active'
                color: EaStyle.Colors.themeForegroundMinor
                text: qsTr('Step %1 of %2').arg(panel.backend.tutorialStepIndex + 1).arg(panel.backend.tutorialStepCount)
            }
            Flow {
                visible: panel.backend.tutorialState === 'active'
                width: parent.width
                spacing: EaStyle.Sizes.fontPixelSize * 0.4
                Repeater {
                    model: panel.backend.tutorialStepCount
                    Rectangle {
                        width: EaStyle.Sizes.fontPixelSize * 0.6
                        height: width
                        radius: width / 2
                        color: index < panel.backend.tutorialStepIndex ? EaStyle.Colors.themeAccent : 'transparent'
                        border.width: 1
                        border.color: index <= panel.backend.tutorialStepIndex ? EaStyle.Colors.themeAccent
                                                                                : EaStyle.Colors.themeForegroundMinor
                    }
                }
            }

            // The step
            Column {
                visible: panel.backend.tutorialState === 'active'
                width: parent.width
                spacing: parent.spacing

                EaElements.Label {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    font.bold: true
                    text: (panel.step.title ?? '') + (panel.step.state === 'done' ? '  ✓' : '')
                }
                EaElements.Label {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    textFormat: Text.MarkdownText
                    text: panel.step.body ?? ''
                    onLinkActivated: (link) => Qt.openUrlExternally(link)
                }
                // Where to go when the frame is not on the control itself
                EaElements.Label {
                    visible: text !== ''
                    width: parent.width
                    wrapMode: Text.WordWrap
                    color: EaStyle.Colors.themeForegroundMinor
                    text: frame.note
                }
                EaElements.Label {
                    visible: text !== ''
                    width: parent.width
                    wrapMode: Text.WordWrap
                    textFormat: Text.MarkdownText
                    color: EaStyle.Colors.themeForegroundHighlight
                    text: panel.showMeError || (panel.step.message ?? '')
                }

                Row {
                    spacing: EaStyle.Sizes.fontPixelSize * 0.5
                    EaElements.Button {
                        text: qsTr('Previous')
                        enabled: panel.backend.tutorialStepIndex > 0
                        onClicked: panel.backend.tutorialPrevious()
                    }
                    EaElements.Button {
                        visible: panel.step.hasCondition ?? false
                        text: qsTr('Show me')
                        ToolTip.visible: hovered
                        ToolTip.text: qsTr('Perform this step')
                        enabled: panel.showMeEnabled
                        onClicked: panel.showMe()
                    }
                    EaElements.Button {
                        text: (panel.step.isLast ?? false) ? qsTr('Finish') : qsTr('Next')
                        enabled: panel.step.canNext ?? false
                        highlighted: panel.step.state === 'done'
                        onClicked: panel.backend.tutorialNext()
                    }
                }
                Row {
                    spacing: EaStyle.Sizes.fontPixelSize
                    EaElements.Button {
                        visible: (panel.step.hasCondition ?? false) && panel.step.state !== 'done'
                        text: qsTr('Skip step')
                        onClicked: panel.backend.tutorialSkip()
                    }
                    EaElements.Button {
                        visible: panel.step.state === 'blocked'
                        text: qsTr('Restart tutorial')
                        onClicked: panel.restart()
                    }
                    EaElements.Button {
                        text: qsTr('Read more')
                        onClicked: Qt.openUrlExternally(panel.backend.homeUrlsDocumentation + (panel.step.more ?? ''))
                    }
                }
            }

            // Finished, or stopped because the session was replaced
            EaElements.Label {
                visible: panel.backend.tutorialState === 'finished' || panel.backend.tutorialState === 'stopped'
                width: parent.width
                wrapMode: Text.WordWrap
                text: panel.backend.tutorialState === 'finished'
                      ? qsTr('You have completed the tutorial.')
                      : panel.backend.tutorialStopReason
            }
            EaElements.Button {
                visible: panel.backend.tutorialState === 'stopped'
                text: qsTr('Restart tutorial')
                onClicked: panel.restart()
            }

            EaElements.Button {
                text: panel.backend.tutorialState === 'active' ? qsTr('Stop') : qsTr('Close')
                onClicked: panel.backend.tutorialStop()
            }
        }
    }

    ///////////////////////
    // The frame around the step's control
    ///////////////////////
    // A child of the panel, which is above the pages; dialogs are in Overlay.overlay and so
    // drawn above both. Its geometry follows the control on a 10 Hz timer, simpler than
    // tracking every ancestor's geometry.
    QtObject {
        id: frame
        property Item item: null
        property string note: ''

        // What to frame for the current step, and what to tell the user when it is not the
        // control itself.
        function resolve() {
            const step = panel.step
            const pageName = (page) => page.charAt(0).toUpperCase() + page.slice(1)
            if (step.page && step.page !== panel.currentPage) {
                return [find(`appbar.${step.page}Tab`), qsTr('Open the %1 page.').arg(pageName(step.page))]
            }
            if (!step.target) {
                return [null, '']
            }
            if (step.sidebarTab) {
                const tab = find(`${step.page}.${step.sidebarTab}Tab`)
                if (tab && !tab.checked) {
                    return [tab, qsTr('Open the %1 tab.').arg(tab.text)]
                }
            }
            const item = find(step.target)
            if (!item) {
                console.warn(`Tutorial target '${step.target}' not found`)
                return [null, '']
            }
            const group = Targets.collapsedGroup(item)
            if (group) {
                return [group, qsTr('Open the %1 group.').arg(group.title)]
            }
            return Targets.isShown(item) ? [item, ''] : [null, qsTr('Scroll the sidebar to bring it into view.')]
        }

        function find(name) {
            return Targets.find(panel.targetRoot, name)
        }
    }

    Timer {
        interval: 100
        repeat: true
        running: panel.backend.tutorialState === 'active'
        triggeredOnStart: true
        onTriggered: {
            const [item, note] = frame.resolve()
            frame.item = item
            frame.note = note
            if (item) {
                const r = item.mapToItem(panel, 0, 0, item.width, item.height)
                highlight.x = r.x - highlight.border.width
                highlight.y = r.y - highlight.border.width
                highlight.width = r.width + 2 * highlight.border.width
                highlight.height = r.height + 2 * highlight.border.width
            }
        }
        onRunningChanged: if (!running) frame.item = null
    }

    Rectangle {
        id: highlight
        visible: frame.item !== null && panel.backend.tutorialState === 'active'
        color: 'transparent'
        // Orange, not the accent blue: the app's own selected tabs, links and buttons are
        // accent blue, and a frame in that colour was hard to tell apart from them.
        border.width: 3
        border.color: EaStyle.Colors.themeForegroundHighlight
        radius: 2
    }

    ///////////////////////
    // Show me
    ///////////////////////
    // Runs the step's actions in order through the real controls, with a pause between them
    // (section 5.6). The step still completes through its condition.
    property bool showingMe: false
    property string showMeError: ''
    property var _actions: []
    property int _waits: 0

    function showMe() {
        showMeError = ''
        // First to where the step is (a no-op when already there), then its own actions.
        const where = []
        if (step.page) {
            where.push({ verb: 'goto', args: [step.page] })
        }
        if (step.sidebarTab) {
            where.push({ verb: 'sidebar-tab', args: [step.sidebarTab] })
        }
        _actions = where.concat(step.actions ?? [])
        _waits = 0
        showingMe = true
        actionTimer.start()
    }

    function stopShowMe(error) {
        actionTimer.stop()
        showingMe = false
        showMeError = error ?? ''
        if (error) {
            console.warn(`Tutorial Show me: ${error}`)
        }
    }

    // Another step: what was running, and its error, belonged to the previous one.
    property string _stepId: ''
    onStepChanged: {
        const stepId = step.id ?? ''
        if (stepId !== _stepId) {
            _stepId = stepId
            stopShowMe()
        }
    }

    Timer {
        id: actionTimer
        interval: 400
        repeat: true
        onTriggered: {
            if (panel._actions.length === 0) {
                panel.stopShowMe()
                return
            }
            const result = panel.perform(panel._actions[0])
            if (result === 'wait') {
                // The control may still be loading, or disabled for a moment.
                if (++panel._waits > 10) {
                    panel.stopShowMe(qsTr('The control for this step is not available.'))
                }
                return
            }
            if (result !== 'done') {
                panel.stopShowMe(result)
                return
            }
            panel._actions = panel._actions.slice(1)
            panel._waits = 0
        }
    }

    // 'done', 'wait' (try again shortly) or an error message.
    function perform(action) {
        const args = action.args
        switch (action.verb) {
        case 'goto':
            return activate(frame.find(`appbar.${args[0]}Tab`))
        case 'sidebar-tab':
            return activate(frame.find(`${step.page}.${args[0]}Tab`))
        case 'click':
            return activate(frame.find(args[0]))
        case 'set':
            return setValue(frame.find(args[0]), args[1])
        case 'call': {
            const [part, slot] = args[0].split('.')
            // `{data}`: the folder of the files the tutorials load
            const values = args.slice(1).map(value => typeof value === 'string'
                                             ? value.replace('{data}', panel.backend.tutorialDataFolder) : value)
            Globals.BackendWrapper.activeBackend[part][slot](...values)
            return 'done'
        }
        }
        return qsTr('Unknown action "%1".').arg(action.verb)
    }

    // A tab button is selected (only if it is not yet: repeating does nothing), a button pressed.
    function activate(item) {
        if (!item || !item.visible || !item.enabled) {
            return 'wait'
        }
        if (item.checkable) {
            if (!item.checked) {
                item.toggle()
            }
        } else {
            item.clicked()
        }
        return 'done'
    }

    // A combo box gets the entry with this text through `activated(index)` alone, which its
    // handler writes back; setting currentIndex would break the control's binding.
    function setValue(item, value) {
        if (!item || !item.visible || !item.enabled) {
            return 'wait'
        }
        if (typeof item.find !== 'function' || item.count === undefined) {
            return qsTr('Show me cannot set this kind of control.')
        }
        const index = item.find(value)
        if (index < 0) {
            return qsTr('There is no entry "%1".').arg(value)
        }
        if (index !== item.currentIndex) {
            item.activated(index)
        }
        return 'done'
    }
}
