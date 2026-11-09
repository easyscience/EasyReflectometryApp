# SPDX-FileCopyrightText: 2026 EasyApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>


#: Set on a parameter the user pinned to a value (an "= value" constraint). A pin is the
#: value and a cleared `free`: a dependency on a constant would collapse the bounds, and
#: the library refuses to load a parameter whose min equals its max. Not saved: the app
#: restores pins from its own constraint records.
PINNED_FLAG = '_easyreflectometryapp_pinned'


def is_independent(parameter) -> bool:
    """Whether `parameter` can be edited, fitted or constrained: neither derived nor pinned."""
    return getattr(parameter, 'independent', True) and not getattr(parameter, PINNED_FLAG, False)


def get_original_name(obj) -> str:
    """Get original name from user_data, with defensive fallback to obj.name.

    Safely handles cases where user_data is None or not a dict.
    """
    user_data = getattr(obj, 'user_data', None)
    if isinstance(user_data, dict):
        return user_data.get('original_name', obj.name)
    return obj.name
