import logging

import numpy as np
from easyreflectometry.data import DataSet1D

from .experiments import CHANNEL_LABELS
from .experiments import channel_shade
from .experiments import experiment_channel_values
from .experiments import flatten_polarized

logger = logging.getLogger(__name__)

# Muted/pastel palette for experiments drawn together, picked by experiment index.
EXPERIMENT_COLORS = [
    '#7BA6C4',  # Soft Blue
    '#E8B889',  # Soft Orange
    '#8DBF8D',  # Soft Green
    '#D48787',  # Soft Red
    '#B296B8',  # Soft Purple
    '#A68F7F',  # Soft Brown
    '#D4A8BC',  # Soft Pink
    '#A5A5A5',  # Soft Gray
    '#B8B87D',  # Soft Olive
    '#7BB8B8',  # Soft Cyan
]


def _empty(name: str) -> DataSet1D:
    return DataSet1D(name=name, x=np.empty(0), y=np.empty(0), ye=np.empty(0), xe=np.empty(0))


def concatenated_experiment_data(project_lib, names: list[str], indices: list[int], visible_channels) -> DataSet1D:
    """The selected experiments' data as one DataSet1D, sorted by x."""
    if not indices:
        return _empty('No experiments selected')

    all_x, all_y, all_ye, all_xe = [], [], [], []
    for exp_idx in indices:
        try:
            data = flatten_polarized(project_lib.experimental_data_for_model_at_index(exp_idx), visible_channels)
            if data.x.size > 0:  # Only include non-empty datasets
                all_x.extend(data.x)
                all_y.extend(data.y)
                all_ye.extend(data.ye if hasattr(data, 'ye') and data.ye.size > 0 else np.zeros_like(data.y))
                all_xe.extend(data.xe if hasattr(data, 'xe') and data.xe.size > 0 else np.zeros_like(data.x))
        except (IndexError, AttributeError) as e:
            logger.warning('Error accessing experiment %s: %s', exp_idx, e)
            continue

    if not all_x:
        return _empty('No valid experiment data')

    # Sort by x values to maintain proper order
    combined_data = sorted(zip(all_x, all_y, all_ye, all_xe), key=lambda item: item[0])
    x_sorted, y_sorted, ye_sorted, xe_sorted = zip(*combined_data)

    exp_names = [names[i] for i in indices if i < len(names)]
    return DataSet1D(
        name=f'Combined: {", ".join(exp_names)}',
        x=np.array(x_sorted),
        y=np.array(y_sorted),
        ye=np.array(ye_sorted),
        xe=np.array(xe_sorted),
    )


def individual_experiment_data_list(
    project_lib,
    names: list[str],
    indices: list[int],
    visible_channels,
    expand_channels: bool = False,
) -> list[dict]:
    """One entry (data, name, color, index, channel) per selected experiment.

    With `expand_channels`, a polarized experiment contributes one entry per
    visible measured channel (each carrying its `channel` and a channel
    shade of the experiment color) instead of being flattened to a single
    one — used by the experiment chart, which draws per-channel series.
    Consumers that are not channel aware yet (analysis, residuals) keep the
    flat one-entry-per-experiment list.
    """
    experiment_data_list = []
    for exp_idx in indices:
        try:
            experiment = project_lib.experimental_data_for_model_at_index(exp_idx)
            exp_name = names[exp_idx] if exp_idx < len(names) else f'Experiment {exp_idx + 1}'
            color = EXPERIMENT_COLORS[exp_idx % len(EXPERIMENT_COLORS)]

            # A polarized experiment contributes one entry per visible
            # measured channel, so nothing the user selected is dropped.
            channels = (
                [channel for channel in experiment_channel_values(experiment) if channel in visible_channels]
                if expand_channels
                else []
            )
            if not channels:
                data = flatten_polarized(experiment, visible_channels)
                if data.x.size > 0:  # Only include non-empty datasets
                    experiment_data_list.append(
                        {'data': data, 'name': exp_name, 'color': color, 'index': exp_idx, 'channel': ''}
                    )
                continue

            for channel in channels:
                data = experiment[channel]
                if data.x.size == 0:
                    continue
                experiment_data_list.append(
                    {
                        'data': data,
                        'name': f'{exp_name} ({CHANNEL_LABELS[channel]} {channel})',
                        'color': channel_shade(color, channel),
                        'index': exp_idx,
                        'channel': channel,
                    }
                )
        except (IndexError, AttributeError, KeyError) as e:
            logger.warning('Error accessing experiment %s: %s', exp_idx, e)
            continue

    return experiment_data_list
