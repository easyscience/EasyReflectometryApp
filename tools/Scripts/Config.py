# SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
# © 2021-2025 Contributors to the EasyReflectometry project <https://github.com/easyScience/EasyReflectometryApp>

__author__ = 'github.com/AndrewSazonov'
__version__ = '0.0.1'

import os
import pathlib
import sys

import Functions


class Config:
    def __init__(self, branch_name=None, matrix_os=None):
        # Main
        self.__dict__ = Functions.config()
        self.os = Functions.osName()
        self.processor = Functions.processor()
        self.branch_name = branch_name
        self.matrix_os = self.matrixOs(matrix_os)

        # Application
        self.app_version = self.__dict__['project']['version']
        self.app_name = self.__dict__['release']['app_name']
        self.family_name = self.__dict__['release']['family_name']
        self.app_file_ext = self.__dict__['ci']['app']['setup']['file_ext'][self.os]
        self.app_full_name = f'{self.app_name}{self.app_file_ext}'

        # Directories
        self.scripts_dir = os.path.normpath(self.__dict__['ci']['project']['subdirs']['scripts'])
        self.build_dir = os.path.normpath(self.__dict__['ci']['project']['subdirs']['build'])
        self.dist_dir = os.path.normpath(self.__dict__['ci']['project']['subdirs']['distribution'])
        self.download_dir = os.path.normpath(self.__dict__['ci']['project']['subdirs']['download'])
        # self.screenshots_dir = os.path.normpath(self.__dict__['ci']['project']['subdirs']['screenshots'])
        # self.tutorials_dir = os.path.normpath(self.__dict__['ci']['project']['subdirs']['tutorials'])
        self.installation_dir = self.installationDir()
        self.installation_dir_for_qtifw = self.installationDirForQtifw()

        # Application setup
        self.setup_os = self.__dict__['ci']['app']['setup']['os'][self.os]
        self.setup_arch = self.__dict__['ci']['app']['setup']['arch'][self.os]
        # self.setup_name_suffix = f'_{self.setup_os}_{self.setup_arch}_v{self.app_version}'
        self.setup_name_suffix = f'_v{self.app_version}_{self.setup_os}'
        if self.matrix_os is not None:
            self.setup_name_suffix = f'_v{self.app_version}_{self.matrix_os}'
        if self.os == 'macos':
            if self.processor == 'i386':
                self.setup_name_suffix = f'{self.setup_name_suffix}-Intel'
            elif self.processor == 'arm':
                self.setup_name_suffix = f'{self.setup_name_suffix}-AppleSilicon'
        self.setup_name = f'{self.app_name}{self.setup_name_suffix}'
        self.setup_file_ext = self.__dict__['ci']['app']['setup']['file_ext'][self.os]
        self.setup_full_name = f'{self.setup_name}{self.setup_file_ext}'
        self.setup_exe_path = os.path.join(self.dist_dir, self.setup_full_name)

        # Artifacts
        self.setup_zip_path_short = self.setupZipPathShort()
        self.setup_zip_path = self.setupZipPath()
        # self.video_tutorial_path = self.videoTutorialPath()

        # Application repository
        self.repository_dir_suffix = self.__dict__['ci']['app']['setup']['repository_dir_suffix']

        # Project
        self.package_name = self.__dict__['project']['name']
        self.license_file = self.__dict__['ci']['project']['license_file']

    def __getitem__(self, key):
        return self.__dict__[key]

    def matrixOs(self, matrix_os):
        # if matrix_os is None:
        #    return None
        # if 'ubuntu-24.04' in matrix_os:
        #    matrix_os = 'ubuntu-22.04'  # NEED FIX: Temporary solution to test the 22.04 build on 24.04
        # elif 'flyci' in matrix_os:
        #    matrix_os = matrix_os.removeprefix('flyci-')  # Simplify the default flyci name
        #    matrix_os = matrix_os.removesuffix('-m2')  # Simplify the default flyci name
        return matrix_os

    # https://doc.qt.io/qtinstallerframework/scripting.html
    def installationDir(self):
        dirs = {
            'macos': {
                '@HomeDir@': str(pathlib.Path.home()),
                '@ApplicationsDir@': '/Applications',
                '@ApplicationsDirUser@': str(pathlib.Path.home().joinpath('Applications')),
            },
            'ubuntu': {'@HomeDir@': str(pathlib.Path.home()), '@ApplicationsDir@': '/opt'},
            'windows': {
                '@HomeDir@': str(pathlib.Path.home()),
                '@ApplicationsDir@': os.getenv('ProgramFiles'),
                '@ApplicationsDirX86@': os.getenv('ProgramFiles(x86)'),
            },
        }
        dir_shortcut = self.__dict__['ci']['app']['setup']['installation_dir_shortcut'][self.os]
        dir = os.path.join(dirs[self.os][dir_shortcut], self.app_name)
        return dir

    def installationDirForQtifw(self):
        dir_shortcut = self.__dict__['ci']['app']['setup']['installation_dir_shortcut'][self.os]
        if self.os == 'macos' and dir_shortcut == '@ApplicationsDir@':
            dir_shortcut = '/Applications'  # @ApplicationsDir@ = @ApplicationsDirUser@ [BUG in QTIFW?]
        dir = os.path.join(dir_shortcut, self.app_name)
        return dir

    def artifactsFileSuffix(self):
        if self.branch_name != 'master' and self.branch_name is not None:
            return f'_{self.branch_name}'
        return ''

    def setupZipPathShort(self):
        setup_zip_name = f'{self.setup_name}.zip'
        setup_zip_path = os.path.join(self.dist_dir, setup_zip_name)
        return setup_zip_path

    def setupZipPath(self):
        file_suffix = self.artifactsFileSuffix()
        setup_zip_name = f'{self.setup_name}{file_suffix}.zip'
        setup_zip_path = os.path.join(self.dist_dir, setup_zip_name)
        return setup_zip_path

    # def videoTutorialPath(self):
    #     file_suffix = self.artifactsFileSuffix()
    #     video_tutorial_name = f'tutorial_{self.setup_name}{file_suffix}.mp4'
    #     video_tutorial_path = os.path.join(self.dist_dir, video_tutorial_name)
    #     return video_tutorial_path


### Main


def main():
    if len(sys.argv) != 4:
        return

    git_branch = sys.argv[1]
    matrix_os = sys.argv[2]
    property_name = sys.argv[3]

    config = Config(git_branch, matrix_os)
    property_value = getattr(config, property_name)

    print(property_value)


if __name__ == '__main__':
    main()
