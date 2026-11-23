// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2021-2025 Contributors to the EasyReflectometry project <https://github.com/easyScience/EasyReflectometryApp>

function Component() {
  //console.log("* isInstaller:", installer.isInstaller())
  //console.log("* isUninstaller:", installer.isUninstaller())
  //console.log("* isUpdater:", installer.isUpdater())
  //console.log("* isPackageManager:", installer.isPackageManager())

  //if (installer.isInstaller() || installer.isUpdater())
  //{
  installer.setDefaultPageVisible(QInstaller.ComponentSelection, false)
  installer.installationStarted.connect(this, Component.prototype.onInstallationStarted)
  if (systemInfo.productType === "windows") { installer.installationFinished.connect(this, Component.prototype.installVCRedist); }
  //}
  //installer.setDefaultPageVisible(QInstaller.LicenseCheck, false)
}

Component.prototype.onInstallationStarted = function () {
  if (component.updateRequested() || component.installationRequested()) {
    if (installer.value("os") == "win") {
      component.installerbaseBinaryPath = "@TargetDir@/signedmaintenancetool.exe"
    }
    installer.setInstallerBaseBinary(component.installerbaseBinaryPath)
  }
}

Component.prototype.installVCRedist = function () {
  var registryVC2017x64 = installer.execute("reg", new Array("QUERY", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64", "/v", "Installed"))[0];
  var install_str = "No";
  var doInstall = false;
  if (!registryVC2017x64) {
    doInstall = true;
    install_str = "Yes";
  }
  else {
    var bld = installer.execute("reg", new Array("QUERY", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64", "/v", "Bld"))[0];
    var elements = bld.split(" ");
    bld = parseInt(elements[elements.length - 1]);
    if (bld < 26706) {
      doInstall = true;
    }
  }
  if (doInstall) {
    QMessageBox.information("vcRedist.install", "Install VS Redistributables", "The application requires Visual Studio 2017 Redistributables. Please follow the steps to install it now.", QMessageBox.OK);
    var dir = installer.value("TargetDir") + "/" + installer.value("ProductName");
    installer.execute(dir + "/VC_redist.x64.exe", "/norestart", "/passive");
  }
}

// here we are creating the operation chain which will be processed at the real installation part later
Component.prototype.createOperations = function () {
  // call default implementation to actually install the registeredfile
  component.createOperations();

  // https://doc.qt.io/qtinstallerframework/operations.html
  if (systemInfo.productType === "windows") {
    // Add desktop shortcut for the app
    component.addOperation(
      "CreateShortcut",
      "@TargetDir@/@ProductName@/@ProductName@.exe",
      "@DesktopDir@/@ProductName@.lnk",
      "workingDirectory=@TargetDir@/@ProductName@",
      "iconPath=@TargetDir@/@ProductName@/@ProductName@.exe", "iconId=0",
      "description=@ProductName@"
    )

    // Add start menu shortcut for the app
    component.addOperation(
      "CreateShortcut",
      "@TargetDir@/@ProductName@/@ProductName@.exe",
      "@StartMenuDir@/@ProductName@/@ProductName@.lnk",
      "workingDirectory=@TargetDir@/@ProductName@",
      "iconPath=@TargetDir@/@ProductName@/@ProductName@.exe", "iconId=0",
      "description=@ProductName@"
    )
    // Add shortcut for maintenance tool.
    component.addOperation(
      "CreateShortcut",
      "@TargetDir@/maintenancetool.exe",
      "@StartMenuDir@/@ProductName@/Maintenance Tool.lnk",
      "workingDirectory=@TargetDir@",
      "iconPath=@TargetDir@/maintenancetool.exe",
      "iconId=0",
      "description=Update or remove@ProductName@");

    // Add start menu shortcut for the app uninstaller
    /*
    component.addOperation(
      "CreateShortcut",
      "@TargetDir@/@ProductName@Uninstaller.exe",
      "@StartMenuDir@/@ProductName@/@ProductName@Uninstaller.lnk",
      "workingDirectory=@TargetDir@",
      "iconPath=@TargetDir@/@ProductName@Uninstaller.exe", "iconId=0",
      "description=@ProductName@Uninstaller"
    )
    */
  }

  if (systemInfo.kernelType === "linux") {
    // App.png is copied to the installation root by MakeInstaller.py, so the
    // path does not depend on PyInstaller's bundle layout (_internal/ etc.).
    var desktopEntry =
      "Type=Application\n" +
      "Name=@ProductName@\n" +
      "GenericName=Reflectometry data analysis\n" +
      "Comment=Making reflectometry data analysis and modelling easy.\n" +
      "Exec=\"@TargetDir@/@ProductName@/@ProductName@\"\n" +
      "Path=@TargetDir@/@ProductName@\n" +
      "Icon=@TargetDir@/App.png\n" +
      "Terminal=false\n" +
      "StartupWMClass=@ProductName@\n" +
      "Categories=Science;Education;"

    // Applications menu / Activities entry. A relative file name is written to
    // $XDG_DATA_HOME/applications (~/.local/share/applications) and removed on
    // uninstall.
    component.addOperation("CreateDesktopEntry", "@ProductName@.desktop", desktopEntry)

    // Desktop icon. The desktop folder is localised (e.g. ~/Schreibtisch), so
    // ask xdg-user-dir for it and fall back to ~/Desktop.
    var desktopDir = ""
    try {
      var result = installer.execute("xdg-user-dir", ["DESKTOP"])
      if (result.length > 1 && result[1] == 0) desktopDir = result[0].trim()
    } catch (e) { }
    if (desktopDir === "") desktopDir = installer.environmentVariable("HOME") + "/Desktop"

    if (installer.fileExists(desktopDir)) {
      var desktopFile = desktopDir + "/@ProductName@.desktop"
      component.addOperation("CreateDesktopEntry", desktopFile, desktopEntry)
      // GNOME (Ubuntu's desktop icons extension) shows a .desktop file on the
      // desktop as a launchable icon only when it is executable and marked
      // trusted; otherwise the user gets an "Allow Launching" prompt or a text
      // file. Run through sh and ignore failures so non-GNOME desktops
      // without gio still install cleanly.
      component.addOperation(
        "Execute",
        "/bin/sh", "-c",
        "chmod +x \"" + desktopFile + "\"; " +
        "gio set \"" + desktopFile + "\" metadata::trusted true 2>/dev/null; true"
      )
    }
  }

}
