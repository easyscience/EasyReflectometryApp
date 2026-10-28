# 5SPDX-FileCopyrightText: 2026 EasyApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>


def get_original_name(obj) -> str:
    """Get original name from user_data, with defensive fallback to obj.name.

    Safely handles cases where user_data is None or not a dict.
    """
    user_data = getattr(obj, 'user_data', None)
    if isinstance(user_data, dict):
        return user_data.get('original_name', obj.name)
    return obj.name
