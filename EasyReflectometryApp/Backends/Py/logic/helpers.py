# 5SPDX-FileCopyrightText: 2025 EasyApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2025 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>


class IO:
    @staticmethod
    def formatMsg(type, *args):
        types = {'main': '*', 'sub': '  -'}
        mark = types[type]
        widths = [22, 21, 20, 10]
        widths[0] -= len(mark)
        msgs = []
        for idx, arg in enumerate(args):
            msgs.append(f'{arg:<{widths[idx]}}')
        msg = ' ▌ '.join(msgs)
        msg = f'{mark} {msg}'
        return msg


def get_original_name(obj) -> str:
    """Get original name from user_data, with defensive fallback to obj.name.

    Safely handles cases where user_data is None or not a dict.
    """
    user_data = getattr(obj, 'user_data', None)
    if isinstance(user_data, dict):
        return user_data.get('original_name', obj.name)
    return obj.name
