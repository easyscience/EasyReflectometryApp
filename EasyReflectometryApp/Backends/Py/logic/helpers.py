# 5SPDX-FileCopyrightText: 2026 EasyApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>


class IO:
    @staticmethod
    def formatMsg(kind, *args):
        marks = {'main': '*', 'sub': '  -'}
        mark = marks[kind]
        widths = [22, 21, 20, 10]
        widths[0] -= len(mark)
        msgs = []
        for idx, arg in enumerate(args):
            # Columns past the last width are not padded.
            width = widths[idx] if idx < len(widths) else 0
            msgs.append(f'{arg:<{width}}')
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
