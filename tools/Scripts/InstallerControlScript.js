// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2021-2025 Contributors to the EasyReflectometry project <https://github.com/easyScience/EasyReflectometryApp>

function Controller() {
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
