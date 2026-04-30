import QtQuick

import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals


EaComponents.AboutDialog {

    visible: EaGlobals.Vars.showAppAboutDialog
    onClosed: EaGlobals.Vars.showAppAboutDialog = false

    appIconPath: Globals.ApplicationInfo.about.icon

    appPrefixName: Globals.ApplicationInfo.about.namePrefixForLogo
    appSuffixName: Globals.ApplicationInfo.about.nameSuffixForLogo
    appVersion: Globals.BackendWrapper.homeVersionNumber
    appDate: Globals.BackendWrapper.homeVersionDate

    appUrl: Globals.BackendWrapper.homeUrlsHomepage
    eulaUrl: Globals.BackendWrapper.homeUrlsLicense
    oslUrl: Globals.BackendWrapper.homeUrlsDependencies

    description: Globals.ApplicationInfo.about.description
    developerIcons: Globals.ApplicationInfo.about.developerIcons
    developerYearsFrom: Globals.ApplicationInfo.about.developerYearsFrom
    developerYearsTo: Globals.ApplicationInfo.about.developerYearsTo

}
