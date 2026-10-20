// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2021-2025 Contributors to the EasyReflectometry project <https://github.com/easyScience/EasyReflectometryApp>

function Controller() {
}

// ---------------------------------------------------------------------------
// Installing over an existing installation (issue #358)
//
// QtIFW refuses a target folder that already holds a MaintenanceTool ("The
// directory you selected already exists and contains an installation") and has
// no setting to allow it. Instead, as soon as such a folder is chosen, offer to
// remove the earlier version with its own MaintenanceTool ("purge" uninstalls
// all components and deletes the folder) and install into the same folder; if
// the user declines, or the removal fails, propose a versioned folder instead.
// ---------------------------------------------------------------------------

// Must match MaintenanceToolName in config.xml (tools/Scripts/MakeInstaller.py).
var MAINTENANCE_TOOL_NAME = "MaintenanceTool"

// State is kept here, not on the Controller: QtIFW calls the page callbacks as
// plain functions (`method.call(arguments)`), so `this` is not the Controller.
// Folders whose existing installation the user has already been asked about.
var askedAboutTargetDir = {}
var targetDirLineEditConnected = false

// The maintenance tool of an installation in `dir`, where QtIFW looks for it.
function maintenanceToolPath(dir) {
  var os = installer.value("os")
  if (os === "mac") {
    return dir + "/" + MAINTENANCE_TOOL_NAME + ".app/Contents/MacOS/" + MAINTENANCE_TOOL_NAME
  }
  if (os === "win") {
    return dir + "/" + MAINTENANCE_TOOL_NAME + ".exe"
  }
  return dir + "/" + MAINTENANCE_TOOL_NAME
}

function containsInstallation(dir) {
  return dir !== "" && installer.fileExists(maintenanceToolPath(dir))
}

// A folder next to `dir` that does not exist yet, named after this version.
function versionedTargetDir(dir) {
  var version = installer.value("ProductVersion")
  var base = version ? dir + "-" + version : dir + "-new"
  var candidate = base
  var counter = 2
  while (installer.fileExists(candidate)) {
    candidate = base + "-" + counter
    counter += 1
  }
  return candidate
}

// Runs the earlier version's own maintenance tool; true if it is gone afterwards.
function removeInstallation(dir) {
  var tool = maintenanceToolPath(dir)
  console.log("* removing the existing installation with: " + tool + " purge")
  installer.execute(tool, ["purge", "--confirm-command", "--accept-messages"])
  return !containsInstallation(dir)
}

Controller.prototype.TargetDirectoryPageCallback = function () {
  if (!installer.isInstaller() || installer.isCommandLineInstance()) {
    return
  }
  var page = gui.currentPageWidget()
  if (page == null) {
    return
  }
  var lineEdit = page.TargetDirectoryLineEdit
  // The callback runs every time the page is entered (also after Back).
  if (!targetDirLineEditConnected) {
    lineEdit.textChanged.connect(onTargetDirChanged)
    targetDirLineEditConnected = true
  }
  onTargetDirChanged(lineEdit.text)
}

function onTargetDirChanged(text) {
  var dir = installer.fromNativeSeparators(String(text).trim())
  // Ask once per folder: typing on past a matching path must not ask again.
  if (!containsInstallation(dir) || askedAboutTargetDir[dir]) {
    return
  }
  askedAboutTargetDir[dir] = true

  var productName = installer.value("ProductName")
  var answer = QMessageBox.question(
    "ExistingInstallation",
    "Existing installation",
    "An earlier version of " + productName + " is installed in\n" + installer.toNativeSeparators(dir) + "\n\n" +
      "Remove it and install this version in its place?\n\n" +
      "Choose No to install this version into a separate folder and keep the earlier one.",
    QMessageBox.Yes | QMessageBox.No,
    QMessageBox.Yes
  )
  if (answer === QMessageBox.Yes) {
    if (removeInstallation(dir)) {
      return // the folder is free now: install into it
    }
    QMessageBox.warning(
      "ExistingInstallationNotRemoved",
      "Existing installation",
      "The earlier version could not be removed. Close " + productName + " if it is running, or remove it " +
        "with the MaintenanceTool in its folder.\n\nThis version will be installed into a separate folder instead.",
      QMessageBox.Ok
    )
  }
  setTargetDir(versionedTargetDir(dir))
}

function setTargetDir(dir) {
  var page = gui.pageWidgetByObjectName("TargetDirectoryPage")
  if (page != null) {
    page.TargetDirectoryLineEdit.setText(installer.toNativeSeparators(dir))
  }
}

Controller.prototype.IntroductionPageCallback = function () {
  var page = gui.currentPageWidget()
  if (page != null) {
    if (installer.isInstaller()) {
      var msg = ""
      msg += "<p>Welcome to the EasyReflectometry Setup Wizard.</p>"
      msg += "<p>EasyReflectometry is a scientific software for modelling and analysis of reflectivity data.</p>"
      msg += "<p>For more details, please visit <a href=\"https://easyreflectometry.org\">https://easyreflectometry.org</a></p>"
      page.MessageLabel.setText(msg)
    }
    if (installer.isUninstaller()) {
      //gui.clickButton(buttons.NextButton)
    }
    if (installer.isUpdater()) {
      //gui.clickButton(buttons.NextButton)
    }
  }
}

Controller.prototype.LicenseAgreementPageCallback = function () {
  //console.log("* enter LicenseAgreementPage")
  //var page = gui.currentPageWidget()
  //if (page != null)
  //{
  //page.AcceptLicenseRadioButton.setChecked(true)
  //}
}

Controller.prototype.FinishedPageCallback = function () {
  //console.log("* buttons, buttons.CommitButton:", buttons, buttons.CommitButton)
  // Try to hide 'Restart' button on the 'Finished' page
  // 1: doesn't work - TypeError: Property 'hide' of object 2 is not a function
  // buttons.CommitButton.hide()
  // 2: doesn't work
  // buttons.CommitButton.enabled = false
  // 3: nothing works
  //buttons.FinishButton.enabled = false
  //buttons.FinishButton.visible = false
  //buttons.CommitButton.visible = false
  //buttons.CommitButton.setVisible(false) // Property 'setVisible' of object 2 is not a function
  // 4: doesn't work
  //buttons[8].enabled = false
  //buttons[8].visible = false
  //buttons[8].setVisible(false)
  //gui.setButtonText(buttons.CommitButton, tr("AAAA"))
  //buttons.RestartButton.visible = false
  //var page = gui.currentPageWidget()
  // 5: doesn't work - TypeError: Cannot call method 'hide' of undefined
  //var page = gui.currentPageWidget()
  //page.CommitButton.hide()
  // 6: doesn't work
  //var page = gui.pageWidgetByObjectName("FinishedPage")
  //var button = gui.findChild(page, "Restart")
  //button.hide()
  //var button2 = gui.findChild(page, "CommitButton")
  //button2.hide()
  // 7:
  //buttons.RestartButton.hide()
}
