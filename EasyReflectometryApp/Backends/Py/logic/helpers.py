# 5SPDX-FileCopyrightText: 2025 EasyApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2025 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

class IO:

    @staticmethod
    def formatMsg(type, *args):
        types = {'main': '*', 'sub': '  -'}
        mark = types[type]
        widths = [22,21,20,10]
        widths[0] -= len(mark)
        msgs = []
        for idx, arg in enumerate(args):
            msgs.append(f'{arg:<{widths[idx]}}')
        msg = ' ▌ '.join(msgs)
        msg = f'{mark} {msg}'
        return msg
