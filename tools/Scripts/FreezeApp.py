# SPDX-FileCopyrightText: 2023 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
# © 2021-2023 Contributors to the EasyReflectometry project <https://github.com/easyScience/EasyReflectometryApp>

import glob
import os
import site
import sys

import Config
import EasyApp
import Functions
import periodictable
import PySide6
import refl1d
import refnx
import shiboken6
from PyInstaller.__main__ import run as pyInstallerMain

CONFIG = Config.Config()


def appIcon():
    icon_dir = os.path.join(*CONFIG['ci']['app']['icon']['dir'])
    icon_name = CONFIG['ci']['app']['icon']['file_name']
    icon_ext = CONFIG['ci']['app']['icon']['file_ext'][CONFIG.os]
    icon_path = os.path.join(CONFIG.package_name, icon_dir, f'{icon_name}{icon_ext}')
    icon_path = os.path.abspath(icon_path)
    return f'--icon={icon_path}'


def excludedModules():
    os_independent = CONFIG['ci']['pyinstaller']['auto_exclude']['all']
    os_dependent = CONFIG['ci']['pyinstaller']['auto_exclude'][CONFIG.os]
    formatted = []
    for module_name in os_independent:
        formatted.append('--exclude-module')
        formatted.append(module_name)
    for module_name in os_dependent:
        formatted.append('--exclude-module')
        formatted.append(module_name)
    return formatted


def addedData():
    # Add main data
    data = [
        {'from': CONFIG.package_name, 'to': CONFIG.package_name},
        {'from': refnx.__path__[0], 'to': 'refnx'},
        {'from': refl1d.__path__[0], 'to': 'refl1d'},
        {'from': periodictable.__path__[0], 'to': 'periodictable'},  #            {'from': cryspy.__path__[0], 'to': 'cryspy'},
        {'from': EasyApp.__path__[0], 'to': 'EasyApp'},
        {'from': 'utils.py', 'to': '.'},
        {'from': 'pyproject.toml', 'to': '.'},
    ]
    # Add other missing libs
    missing_other_libraries = CONFIG['ci']['pyinstaller']['missing_other_libraries'][CONFIG.os]
    if missing_other_libraries:
        for lib_file in missing_other_libraries:
            data.append({'from': lib_file, 'to': '.'})
    # Add missing calculator libs
    site_packages_path = site.getsitepackages()[
        -1
    ]  # use the last element, since on certain conda installations we get more than one entry
    missing_calculator_libs = CONFIG['ci']['pyinstaller']['missing_calculator_libs'][CONFIG.os]
    if missing_calculator_libs:
        for lib_name in missing_calculator_libs:
            lib_path = os.path.join(site_packages_path, lib_name)
            data.append({'from': lib_path, 'to': lib_name})
    # Format for pyinstaller
    separator = CONFIG['ci']['pyinstaller']['separator'][CONFIG.os]
    formatted = []
    for element in data:
        formatted.append(f'--add-data={element["from"]}{separator}{element["to"]}')
    return formatted


def copyMissingLibs():
    missing_files = CONFIG['ci']['pyinstaller']['missing_pyside6_files'][CONFIG.os]
    if len(missing_files) == 0:
        Functions.printNeutralMessage(f'No missing PySide6 libraries for {CONFIG.os}')
        return
    try:
        message = 'copy missing PySide6 libraries'
        pyside6_path = PySide6.__path__[0]
        shiboken6_path = shiboken6.__path__[0]
        for file_name in missing_files:
            file_path = os.path.join(shiboken6_path, file_name)
            for file_path in glob.glob(file_path):  # for cases with '*' in the lib name
                Functions.copyFile(file_path, pyside6_path)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def copyMissingPlugins():
    missing_plugins = CONFIG['ci']['pyinstaller']['missing_pyside6_plugins'][CONFIG.os]
    if len(missing_plugins) == 0:
        Functions.printNeutralMessage(f'No missing PySide6 plugins for {CONFIG.os}')
        return
    try:
        message = 'copy missing PySide6 plugins'
        pyside6_path = PySide6.__path__[0]
        app_plugins_path = os.path.join(CONFIG.dist_dir, CONFIG.app_name, 'PySide6', 'plugins')
        for relative_dir_path in missing_plugins:
            src_dir_name = os.path.basename(relative_dir_path)
            src_dir_path = os.path.join(pyside6_path, relative_dir_path)
            dst_dir_path = os.path.join(app_plugins_path, src_dir_name)
            Functions.copyDir(src_dir_path, dst_dir_path)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def excludeFiles():
    file_names = CONFIG['ci']['pyinstaller']['manual_exclude']
    if len(file_names) == 0:
        Functions.printNeutralMessage(f'No libraries to be excluded for {CONFIG.os}')
        return
    try:
        message = 'exclude files'
        for file_name in file_names:
            dir_suffix = CONFIG['ci']['pyinstaller']['dir_suffix'][CONFIG.os]
            content_suffix = CONFIG['ci']['pyinstaller']['content_suffix'][CONFIG.os]
            freezed_app_path = os.path.join(CONFIG.dist_dir, f'{CONFIG.app_name}{dir_suffix}', f'{content_suffix}')
            file_path = os.path.join(freezed_app_path, file_name)
            for file_path in glob.glob(file_path):  # for cases with '*' in the lib name
                Functions.removeFile(file_path)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def runPyInstaller():
    try:
        message = 'freeze app'
        main_py_path = os.path.join(CONFIG.package_name, 'main.py')
        pyInstallerMain(
            [
                main_py_path,  # Application main file
                f'--name={CONFIG.app_name}',  # Name to assign to the bundled app and spec file (default: first script’s basename)
                '--log-level',
                'WARN',  # LEVEL may be one of DEBUG, INFO, WARN, ERROR, CRITICAL (default: INFO).
                # Needed for reportlab
                '--noconfirm',  # Replace output directory (default: SPECPATH/dist/SPECNAME) without asking for confirmation
                '--clean',  # Clean PyInstaller cache and remove temporary files before building
                #'--windowed',  # Windows and Mac OS X: do not provide a console window for standard i/o.
                #'--onedir',  # Create a one-folder bundle containing an executable (default)
                #'--target-architecture', 'universal2', # Target architecture (macOS only; valid values: x86_64, arm64, universal2). Error: _multiarray_tests.cpython-311-darwin.so is not a fat binary! (i.e. not multi-architecture)
                #'--specpath', workDirPath(),           # Folder to store the generated spec file (default: current directory)
                '--distpath',
                CONFIG.dist_dir,  # Where to put the bundled app (default: ./dist)
                '--workpath',
                CONFIG.build_dir,  # Where to put all the temporary work files, .log, .pyz and etc. (default: ./build)
                '--collect-all',
                'reportlab.graphics.barcode',
                *excludedModules(),  # Exclude modules
                *addedData(),  # Add data
                appIcon(),  # Application icon
            ]
        )
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


if __name__ == '__main__':
    copyMissingLibs()
    copyMissingPlugins()
    runPyInstaller()
    excludeFiles()
