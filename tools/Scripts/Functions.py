# SPDX-FileCopyrightText: 2023 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
# © 2021-2023 Contributors to the EasyReflectometry project <https://github.com/easyScience/EasyReflectometryApp>

__author__ = 'github.com/AndrewSazonov'
__version__ = '0.0.1'

import os
import platform
import shutil
import subprocess
import sys
import zipfile

import requests
import toml

# FUNCTIONS


def coloredText(message='', style='1', background_color='49m', text_color='39'):
    # http://ozzmaker.com/add-colour-to-text-in-python/
    escape = '\033['
    reset = '0m'
    return f'{escape}{style};{text_color};{background_color}{message}{escape}{reset}'


def printFailMessage(message, exception=None):
    bright_red = '31'
    extended_message = f'- Failed to {message}'
    if exception:
        extended_message += os.linesep
        extended_message += str(exception)
    report = coloredText(message=extended_message, text_color=bright_red)
    print(report)


def printSuccessMessage(message):
    bright_green = '32'
    extended_message = f'+ Succeeded to {message}'
    report = coloredText(message=extended_message, text_color=bright_green)
    print(report)


def printNeutralMessage(message):
    bright_blue = '34'
    extended_message = f'* {message}'
    report = coloredText(message=extended_message, text_color=bright_blue)
    print(report)


def run(*args):
    printNeutralMessage(' '.join(args))
    subprocess.run(
        args,
        capture_output=False,
        universal_newlines=True,  # converts the output to a string instead of a byte array.
        # check=True                  # forces the Python method to throw an exception if the underlying process
        # encounters errors
    )


def downloadFile(url, destination):
    if os.path.exists(destination):
        printNeutralMessage(f'File already exists {destination}')
        return
    try:
        message = f'download from {url}'
        file = requests.get(url, allow_redirects=True)
        open(destination, 'wb').write(file.content)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def attachDmg(file):
    try:
        message = f'attach {file}'
        run('hdiutil', 'attach', file)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def installSilently(installer, silent_script, sudo=False):
    try:
        message = f'run installer {installer}'
        args = [installer, '--verbose', '--script', silent_script]
        if sudo:
            args = ['sudo', *args]
        run(*args)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def config():
    return toml.load(os.path.join(os.getcwd(), 'pyproject.toml'))


def osName():
    platform = sys.platform
    if platform.startswith('darwin'):
        return 'macos'
    elif platform.startswith('lin'):
        return 'ubuntu'
    elif platform.startswith('win'):
        return 'windows'
    else:
        print("- Unsupported platform '{0}'".format(platform))
        return None


def processor():
    return platform.processor()


def environmentVariable(name, default=None):
    value = os.getenv(name)
    if value is not None:
        return value
    else:
        printNeutralMessage(f'Environment variable {name} is not found, using default value {default}')
        return default


def setEnvironmentVariable(name, value):
    try:
        message = f'set environment variable {name} to {value}'
        os.environ[name] = value
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def addReadPermission(file):
    try:
        message = f'add read permissions to {file}'
        run('chmod', 'a+x', file)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def createFile(path, content):
    if os.path.exists(path):
        printNeutralMessage(f'File already exists {path}')
        return
    try:
        message = f'create file {path}'
        with open(path, 'w') as file:
            file.write(content)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def copyFile(source, destination):
    path = os.path.join(destination, os.path.basename(source))
    if os.path.exists(path):
        printNeutralMessage(f'File already exists {path}')
        return
    try:
        message = f'copy file {source} to {destination}'
        shutil.copy2(source, destination, follow_symlinks=True)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit(1)
    else:
        printSuccessMessage(message)


def removeFile(path):
    if not os.path.exists(path):
        printNeutralMessage(f'File does not exist {path}')
        return
    try:
        message = f'delete file {path}'
        os.remove(path)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def createDir(path):
    if os.path.exists(path):
        printNeutralMessage(f'Directory already exists {path}')
        return
    try:
        message = f'create dir {path}'
        os.makedirs(path)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def copyDir(source, destination):
    path = os.path.join(destination, os.path.basename(source))
    if os.path.exists(path):
        printNeutralMessage(f'Directory already exists {path}')
        return
    try:
        message = f'copy dir {source} to {destination}'
        shutil.copytree(source, destination, dirs_exist_ok=True)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def moveDir(source, destination):
    path = os.path.join(destination, os.path.basename(source))
    if os.path.exists(path):
        printNeutralMessage(f'Directory already exists {path}')
        return
    try:
        message = f'move dir {source} to {destination}'
        shutil.move(source, destination)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def dict2xml(d, root_node=None, add_xml_version=True):
    wrap = False if root_node is None or isinstance(d, list) else True
    root = 'root' if root_node is None else root_node
    xml = ''
    attr = ''
    children = []

    if add_xml_version:
        xml += '<?xml version="1.0" ?>'

    if isinstance(d, dict):
        for key, value in dict.items(d):
            if isinstance(value, (dict, list)):
                children.append(dict2xml(value, root_node=key, add_xml_version=False))
            elif key[0] == '@':
                attr = attr + ' ' + key[1::] + '="' + str(value) + '"'
            else:
                xml = '<' + key + '>' + str(value) + '</' + key + '>'
                children.append(xml)

    elif isinstance(d, list):
        for value in d:
            children.append(dict2xml(value, root_node=root, add_xml_version=False))

    else:
        raise TypeError(f'Type {type(d)} is not supported')

    end_tag = '>' if children else '/>'

    if wrap:
        xml = '<' + root + attr + end_tag

    if children:
        xml += ''.join(children)

        if wrap:
            xml += '</' + root + '>'

    return xml


def unzip(archive_path, destination_dir):
    try:
        message = f'unzip {archive_path} to {destination_dir}'
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(destination_dir)
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)


def zip(source, destination):
    # https://thispointer.com/python-how-to-create-a-zip-archive-from-multiple-files-or-directory/
    # https://stackoverflow.com/questions/27991745/zip-file-and-avoid-directory-structure
    # https://stackoverflow.com/questions/32640053/compressing-directory-using-shutil-make-archive-while-preserving-directory-str
    # Zip all the files from given directory
    """
    Compress a file/directory.
    """
    # Check if src exists
    if not os.path.exists(source):
        printFailMessage(f"zip file/directory (it doesn't exist): {source}")
        sys.exit()
        return
    # create a ZipFile object
    try:
        with zipfile.ZipFile(destination, 'w') as zf:
            rootdirname = os.path.basename(source)
            if os.path.isfile(source):
                message = f'zip file {source} to {destination}'
                filepath = source
                parentpath = os.path.relpath(filepath, source)
                arcpath = os.path.join(rootdirname, parentpath)
                zf.write(filepath, arcpath)
            elif os.path.isdir(source):
                message = f'zip dir {source} to {destination}'
                for dirpath, _, filenames in os.walk(source):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        parentpath = os.path.relpath(filepath, source)
                        arcpath = os.path.join(rootdirname, parentpath)
                        zf.write(filepath, arcpath)
            else:
                printFailMessage(message + ': It is a special file (socket, FIFO, device file)')
                sys.exit()
    except Exception as exception:
        printFailMessage(message, exception)
        sys.exit()
    else:
        printSuccessMessage(message)
