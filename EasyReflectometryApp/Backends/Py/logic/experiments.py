import colorsys
import logging

from easyreflectometry import Project as ProjectLib

logger = logging.getLogger(__name__)

# Fixed per-channel colors for polarized experiments (pp, pm, mp, mm), matching
# the channel order used across the app and the report.
CHANNEL_COLORS = {'pp': '#0173B2', 'pm': '#029E73', 'mp': '#CC78BC', 'mm': '#DE8F05'}
CHANNEL_LABELS = {'pp': '↑↑', 'pm': '↑↓', 'mp': '↓↑', 'mm': '↓↓'}

# When several experiments share a chart, the experiment color carries the hue
# and the channel is distinguished by lightness — so a channel is still
# recognisable without two experiments ending up with the same color.
_CHANNEL_LIGHTNESS_SHIFT = {'pp': -0.12, 'pm': 0.0, 'mp': 0.12, 'mm': 0.24}


def channel_shade(base_color: str, channel: str) -> str:
    """A per-channel variant of an experiment color (same hue, shifted lightness)."""
    shift = _CHANNEL_LIGHTNESS_SHIFT.get(channel)
    color = base_color.lstrip('#')
    if shift is None or len(color) != 6:
        return base_color
    try:
        red, green, blue = (int(color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return base_color
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    lightness = min(0.88, max(0.18, lightness + shift))
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return '#{:02X}{:02X}{:02X}'.format(round(red * 255), round(green * 255), round(blue * 255))


def flatten_polarized(experiment, visible_channels=None):
    """A flat ``DataSet1D`` for consumers that expect one x/y/ye series.

    Unpolarized experiments are returned unchanged. For a `PolarizedDataSet`
    the first measured channel is returned — restricted to `visible_channels`
    (channel-value strings) when given and matching. Fully per-channel display
    goes through the dedicated channel-aware code paths instead.
    """
    channels = getattr(experiment, 'available_channels', None)
    if channels is None:
        return experiment
    if visible_channels:
        for channel in channels:
            if channel.value in visible_channels:
                return experiment[channel]
    return experiment[channels[0]]


def experiment_channel_values(experiment) -> list[str]:
    """Measured channel-value strings of an experiment ([] when unpolarized)."""
    channels = getattr(experiment, 'available_channels', None)
    if channels is None:
        return []
    return [channel.value for channel in channels]


def ordered_experiment_items(project_lib: ProjectLib) -> list[tuple[object, object]]:
    """Experiments as ``(key, experiment)`` pairs, in the order the UI lists them.

    The UI addresses experiments by list position; this is the one place that
    order is defined. Supports mapping-like storage without assuming contiguous
    integer keys.
    """
    experiments = project_lib._experiments
    if not experiments:
        return []

    if hasattr(experiments, 'items'):
        items = list(experiments.items())
        try:
            items.sort(key=lambda item: item[0])
        except TypeError:
            pass
        return items

    return list(enumerate(experiments))


def ordered_experiments(project_lib: ProjectLib) -> list:
    """Experiment objects in the order of :func:`ordered_experiment_items`."""
    return [experiment for _, experiment in ordered_experiment_items(project_lib)]


class Experiments:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib

    def _experiment_at_index(self, index: int):
        items = ordered_experiment_items(self._project_lib)
        if 0 <= index < len(items):
            return items[index][1]
        return None

    def _experiment_key_at_index(self, index: int):
        items = ordered_experiment_items(self._project_lib)
        if 0 <= index < len(items):
            return items[index][0]
        return None

    def available(self) -> list[str]:
        experiments_name = []
        try:
            for _, exp in ordered_experiment_items(self._project_lib):
                experiments_name.append(exp.name)
        except IndexError:
            pass
        return experiments_name

    def polarized_flags(self) -> list[bool]:
        """Per-experiment flag: True when the experiment carries per-channel (polarized) data."""
        return [
            getattr(exp, 'available_channels', None) is not None for _, exp in ordered_experiment_items(self._project_lib)
        ]

    def channel_counts(self) -> list[int]:
        """Per-experiment number of measured spin channels (0 when unpolarized)."""
        return [len(experiment_channel_values(exp)) for _, exp in ordered_experiment_items(self._project_lib)]

    def current_index(self) -> int:
        return self._project_lib._current_experiment_index

    def set_current_index(self, new_value: int) -> bool:
        if new_value != self._project_lib._current_experiment_index:
            self._project_lib._current_experiment_index = new_value
            return True
        return False

    def set_experiment_name(self, new_name: str) -> None:
        exp = self._experiment_at_index(self._project_lib._current_experiment_index)
        if exp:
            exp.name = new_name

    def set_experiment_name_at_index(self, index: int, new_name: str) -> None:
        exp = self._experiment_at_index(index)
        if exp:
            exp.name = new_name

    def model_indices(self) -> list[int]:
        """Per experiment, the index of its model (-1 when it has none)."""
        indices = []
        for key, _ in ordered_experiment_items(self._project_lib):
            index = self._project_lib.model_index_for_experiment(key)
            indices.append(-1 if index is None else index)
        return indices

    def model_index_on_experiment(self) -> int:
        indices = self.model_indices()
        current = self._project_lib._current_experiment_index
        return indices[current] if 0 <= current < len(indices) else -1

    def set_model_on_experiment(self, index: int, model_index: int) -> bool:
        """Bind the experiment at `index` to the model at `model_index`; whether it changed."""
        key = self._experiment_key_at_index(index)
        if key is None or not 0 <= model_index < len(self._project_lib._models):
            logger.warning('Cannot bind experiment %s to model %s.', index, model_index)
            return False
        if self._project_lib.model_index_for_experiment(key) == model_index:
            return False
        self._project_lib.set_model_for_experiment(key, model_index)
        return True

    def included_in_fit(self) -> list[bool]:
        """Per experiment, whether the next fit includes it."""
        return [experiment.include_in_fit for _, experiment in ordered_experiment_items(self._project_lib)]

    def set_included_in_fit(self, index: int, included: bool) -> bool:
        experiment = self._experiment_at_index(index)
        if experiment is None or experiment.include_in_fit == included:
            return False
        experiment.include_in_fit = included
        return True

    def remove_experiment(self, index: int) -> dict:
        """Remove the experiment at the given (ordered) index; returns the library's old -> new
        key table of the remaining ones (empty when nothing was removed)."""
        key = self._experiment_key_at_index(index)
        if key is None:
            logger.warning('Experiment index %s is out of range.', index)
            return {}
        return self._project_lib.remove_experiment(key)
