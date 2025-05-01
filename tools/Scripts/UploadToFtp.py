# SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
# © 2021-2025 Contributors to the EasyReflectometry project <https://github.com/easyScience/EasyReflectometryApp>

__author__ = 'github.com/AndrewSazonov'
__version__ = '0.0.1'

import ftplib
import os
import pathlib
import sys

import Config
import Functions

CONFIG = Config.Config(sys.argv[1], sys.argv[2])

FTP_PASSWORD = sys.argv[3]


def connect(ftp, host, port):
    try:
        message = f'connect to ftp server'
        ftp.connect(host, port)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def login(ftp, user, password):
    try:
        message = f'login to ftp server'
        ftp.login(user, password)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def winToLin(path):
    return path.replace('\\', '/')


def makeDir(ftp, path):
    if pathExists(ftp, path):
        Functions.printNeutralMessage(f'Directory exists: {path}')
        return
    try:
        path = winToLin(path)
        message = f'create directory {path}'
        ftp.mkd(path)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def uploadFile(ftp, source, destination):
    try:
        destination = winToLin(destination)
        message = f'upload file {source} to {destination}'
        dir_name = os.path.basename(destination)
        dir_names = ftp.nlst(os.path.dirname(destination))
        if dir_name not in dir_names:
            makeDir(ftp, destination)
        destination = f'{destination}/{os.path.basename(source)}'
        with open(source, 'rb') as fb:
            ftp.storbinary(f'STOR {destination}', fb)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def uploadDir(ftp, source, destination):
    try:
        message = f'upload dir {source} to {destination}'
        root_dir_name = os.path.basename(source)
        for dir_path, _, file_names in os.walk(source):
            for file_name in file_names:
                source_file = os.path.join(dir_path, file_name)
                parent_path = os.path.relpath(source_file, source)
                parent_dir = os.path.dirname(parent_path)
                destination_dir = os.path.join(destination, root_dir_name, parent_dir).rstrip(os.path.sep)
                uploadFile(ftp, source_file, destination_dir)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def upload(ftp, source, destination):
    try:
        message = f'upload {source} to {destination}'
        if os.path.isfile(source):
            uploadFile(ftp, source, destination)
        elif os.path.isdir(source):
            uploadDir(ftp, source, destination)
        else:
            Functions.printFailMessage(message)
            sys.exit(1)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def pathExists(ftp, path):
    try:
        message = f'find path {path}'
        ftp.nlst(path)
    except Exception as exception:
        Functions.printFailMessage(message, exception)
        return False
    else:
        Functions.printSuccessMessage(message)
        return True


def removeDir(ftp, path):
    if not pathExists(ftp, path):
        Functions.printNeutralMessage(f"Directory doesn't exists: {path}")
        return
    try:
        path = winToLin(path)
        message = f'remove directory {path}'
        for name, properties in ftp.mlsd(path=path):
            if name in ['.', '..']:
                continue
            elif properties['type'] == 'file':
                ftp.delete(f'{path}/{name}')
            elif properties['type'] == 'dir':
                removeDir(ftp, f'{path}/{name}')
        ftp.rmd(path)
    except Exception as exception:
        Functions.printNeutralMessage(message, exception)
        sys.exit(1)
    else:
        Functions.printSuccessMessage(message)


def deploy():
    host = CONFIG['ci']['app']['setup']['ftp']['host']
    port = CONFIG['ci']['app']['setup']['ftp']['port']
    user = CONFIG['ci']['app']['setup']['ftp']['user']
    prefix = CONFIG['ci']['app']['setup']['ftp']['prefix']
    repo_subdir = CONFIG['ci']['app']['setup']['ftp']['repo_subdir']

    local_repository_dir_name = f'{CONFIG.app_name}{CONFIG.repository_dir_suffix}'
    local_repository_dir_path = os.path.join(CONFIG.dist_dir, local_repository_dir_name, CONFIG.setup_os)
    online_repository_subdir_path = f'{prefix}/{repo_subdir}'
    online_repository_dir_path = f'{online_repository_subdir_path}/{CONFIG.setup_os}'

    # Functions.printNeutralMessage(f'local_repository_dir_path {local_repository_dir_path}')
    # Functions.printNeutralMessage(f'online_repository_dir_path {online_repository_dir_path}')
    # Functions.printNeutralMessage(f'host:port {host}:{port}')

    ftp = ftplib.FTP()
    connect(ftp, host, port)
    login(ftp, user, FTP_PASSWORD)
    removeDir(ftp, online_repository_dir_path)
    makeDir(ftp, online_repository_dir_path)
    upload(ftp, local_repository_dir_path, online_repository_subdir_path)
    ftp.quit()


if __name__ == '__main__':
    deploy()
