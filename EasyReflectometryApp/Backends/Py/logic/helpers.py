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


def set_value_widening_bounds(parameter, value: float) -> None:
    """Set the value the user entered, moving the bound it lies past.

    For the Sample page's edits, which have no bound cells beside them: the core
    would clamp the value to the default window the library put around the
    parameter. The user's value wins, and the widened bound shows red in the
    Analysis table when it is unphysical (see `parameters.physical_range`). Not
    for parameters whose bounds are their domain (an angle's 0-360).
    """
    if value < parameter.min:
        parameter.min = value
    elif value > parameter.max:
        parameter.max = value
    parameter.value = value


def set_bound(parameter, bound: str, value: float) -> None:
    """Set `parameter`'s 'min' or 'max' bound to the value the user entered.

    The core refuses a bound past the current value; the value is moved onto the
    bound first, so the bound the user set is the one the fit uses. A bound that
    leaves no room (min at or above max) raises ValueError and changes nothing.
    """
    if bound == 'min':
        if value >= parameter.max:
            raise ValueError(f'The min ({value}) must be below the max ({parameter.max}).')
        if value > parameter.value:
            parameter.value = value
    elif bound == 'max':
        if value <= parameter.min:
            raise ValueError(f'The max ({value}) must be above the min ({parameter.min}).')
        if value < parameter.value:
            parameter.value = value
    else:
        raise ValueError(f"Unknown bound {bound!r}, expected 'min' or 'max'.")
    setattr(parameter, bound, value)


def get_original_name(obj) -> str:
    """Get original name from user_data, with defensive fallback to obj.name.

    Safely handles cases where user_data is None or not a dict.
    """
    user_data = getattr(obj, 'user_data', None)
    if isinstance(user_data, dict):
        return user_data.get('original_name', obj.name)
    return obj.name
