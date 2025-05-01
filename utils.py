# SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
# © 2021-2025 Contributors to the EasyReflectometry project <https://github.com/easyScience/EasyReflectometryApp>

import argparse
import datetime
import os
import sys

import pip
import toml

### Get value from pyproject.toml


def conf():
    project_fname = 'pyproject.toml'
    current_path = os.path.dirname(__file__)
    project_fpath = os.path.join(current_path, project_fname)
    return toml.load(project_fpath)


def keyPath():
    if len(sys.argv) < 2:
        return ''
    return sys.argv[1]


def getValue(d, element):
    keys = element.split('.')
    keys[-1] = keys[-1].split('-')[0]  # macos-latest -> macos, etc.
    rv = d
    for key in keys:
        rv = rv[key]
    return rv


### Update pyproject.toml


def extraDict():
    python_packages_path = os.path.dirname(pip.__path__[0]).replace('\\', '/')

    dt = datetime.datetime.now()
    build_date = f'{dt.day} {dt:%b} {dt.year}'  # e.g. 3 Jun 2021
    date_for_qtifw = f'{dt.year}-{dt:%m}-{dt:%d}'  # e.g. 2021-06-03

    github_server_url = os.getenv('GITHUB_SERVER_URL', '')
    github_repo = os.getenv('GITHUB_REPOSITORY', '')
    github_repo_url = f'{github_server_url}/{github_repo}'

    branch_name = os.getenv('BRANCH_NAME', '')
    branch_url = f'{github_repo_url}/tree/{branch_name}'

    commit_sha = os.getenv('GITHUB_SHA', '')
    commit_sha_short = commit_sha[:6]
    commit_url = f'{github_repo_url}/commit/{commit_sha}'

    app_version = getValue(conf(), 'project.version')
    release_tag = f'v{app_version}'
    release_title = f'Version {app_version} ({build_date})'

    return {
        'ci': {
            'cache': {'python_packages_path': python_packages_path},
            'app': {
                'info': {
                    'build_date': build_date,
                    'date_for_qtifw': date_for_qtifw,
                    'release_tag': release_tag,
                    'release_title': release_title,
                    'branch_name': branch_name,
                    'branch_url': branch_url,
                    'commit_sha_short': commit_sha_short,
                    'commit_url': commit_url,
                }
            },
        }
    }


def extraToml():
    return toml.dumps(extraDict())


def updatePyprojectToml():
    with open('pyproject.toml', 'r', encoding='utf-8') as f:
        pyproject_toml = f.read()
    pyproject_toml += '\n' + extraToml()
    with open('pyproject.toml', 'w', encoding='utf-8') as f:
        f.write(pyproject_toml)


### Main


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--get', dest='key', type=str, help='get parameter value by key from pyproject.toml')
    parser.add_argument('-u', '--update', action='store_true', help='add extra info to the pyproject.toml')
    args = parser.parse_args()
    if args.key:
        value = getValue(conf(), args.key)
        print(value)
    if args.update:
        updatePyprojectToml()


if __name__ == '__main__':
    main()
