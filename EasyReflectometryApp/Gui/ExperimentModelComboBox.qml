import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

// Table cell choosing the model an experiment is fitted with. Shows the stored
// pairing (blank when the experiment has none) and changes only that experiment.
EaComponents.TableViewComboBox {
    // The experiment's row in the experiment tables
    required property int row

    horizontalAlignment: Text.AlignLeft
    // Model names are plain text, and Text does not elide rich text (EasyApp's
    // default): a long name would run over the drop-down arrow. Plain, it is
    // shortened in the middle, keeping the substrate and the superphase.
    textFormat: Text.PlainText
    model: Globals.BackendWrapper.sampleModelNames
    currentIndex: Globals.BackendWrapper.analysisExperimentsModelIndices[row] ?? -1
    onActivated: {
        Globals.BackendWrapper.analysisSetModelOnExperiment(row, currentIndex)
        // Choosing an entry replaces the binding; restore it so the combo keeps
        // showing the stored pairing.
        currentIndex = Qt.binding(() => Globals.BackendWrapper.analysisExperimentsModelIndices[row] ?? -1)
    }

    // The whole name of a shortened one
    ToolTip.visible: hovered && !popup.visible && contentItemLabel.truncated
    ToolTip.text: displayText

    // The list shows whole names, which differ in the middle as often as at the
    // ends: as wide as its longest item (within the sidebar), growing leftwards
    // over the name column rather than past the sidebar's edge. Sized from the
    // items as laid out, not from font metrics: those keep the measurement of
    // the fallback font when EasyApp's own is loaded later.
    popup.width: {
        let widest = width
        for (const item of popup.contentItem.contentItem.children) {
            if (item.contentItem)
                widest = Math.max(widest, item.contentItem.implicitWidth + item.leftPadding + item.rightPadding)
        }
        return Math.min(widest, EaStyle.Sizes.sideBarContentWidth)
    }
    popup.x: width - popup.width
}
