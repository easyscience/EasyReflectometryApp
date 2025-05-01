# SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
# © 2021-2025 Contributors to the EasyReflectometry project <https://github.com/easyScience/EasyReflectometryApp>

__author__ = 'github.com/AndrewSazonov'
__version__ = '0.0.1'

import os
import sys

import Config
import Functions

CONFIG = Config.Config(sys.argv[1], sys.argv[2])


def setupExePath():
    d = {
        'macos': os.path.join(CONFIG.setup_full_name, 'Contents', 'MacOS', CONFIG.setup_name),
        'ubuntu': CONFIG.setup_full_name,
        'windows': CONFIG.setup_full_name,
    }
    return os.path.join(CONFIG.dist_dir, d[CONFIG.os])


def fixPermissions():
    if CONFIG.os == 'macos' or 'ubuntu':
        try:
            message = f'fixing permissions for os {CONFIG.os}'
            Functions.run('chmod', '+x', setupExePath())
        except Exception as exception:
            Functions.printFailMessage(message, exception)
            sys.exit(1)
        else:
            Functions.printSuccessMessage(message)
    else:
        Functions.printNeutralMessage(f'No fixing permissions needed for os {CONFIG.os}')


def runInstallerSilently():
    try:
        message = f'install {CONFIG.app_name}'
        Functions.run(setupExePath(), 'install', '--verbose', '--confirm-command', '--default-answer', '--accept-licenses')
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


if __name__ == '__main__':
    fixPermissions()
    runInstallerSilently()
