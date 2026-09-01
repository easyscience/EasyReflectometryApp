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


class Experiments:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib

    def _ordered_experiment_items(self) -> list[tuple[object, object]]:
        """Return experiments as ordered ``(key, experiment)`` pairs.

        Supports mapping-like storage without assuming contiguous integer keys.
        """
        experiments = self._project_lib._experiments
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

    def _experiment_at_index(self, index: int):
        items = self._ordered_experiment_items()
        if 0 <= index < len(items):
            return items[index][1]
        return None

    def _experiment_key_at_index(self, index: int):
        items = self._ordered_experiment_items()
        if 0 <= index < len(items):
            return items[index][0]
        return None

    def available(self) -> list[str]:
        experiments_name = []
        try:
            for _, exp in self._ordered_experiment_items():
                experiments_name.append(exp.name)
        except IndexError:
            pass
        return experiments_name

    def polarized_flags(self) -> list[bool]:
        """Per-experiment flag: True when the experiment carries per-channel (polarized) data."""
        return [
            getattr(exp, 'available_channels', None) is not None for _, exp in self._ordered_experiment_items()
        ]

    def channel_counts(self) -> list[int]:
        """Per-experiment number of measured spin channels (0 when unpolarized)."""
        return [len(experiment_channel_values(exp)) for _, exp in self._ordered_experiment_items()]

    def current_index(self) -> int:
        return self._project_lib._current_experiment_index

    def set_current_index(self, new_value: int) -> None:
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

    def model_on_experiment(self, experiment_index: int = -1) -> dict:
        if experiment_index == -1:
            experiment_index = self._project_lib._current_experiment_index
        exp = self._experiment_at_index(experiment_index)
        if exp:
            return exp.model
        return {}

    def model_index_on_experiment(self) -> int:
        model = self.model_on_experiment()
        if model:
            return self._project_lib._models.index(model)
        return -1

    def set_model_on_experiment(self, new_value: int) -> None:
        exp = self._experiment_at_index(self._project_lib._current_experiment_index)
        models = self._project_lib._models
        if exp and models:
            try:
                model = models[new_value]
                exp.model = model
            except IndexError:
                logger.warning('Model index %s is out of range for the current experiment.', new_value)
        else:
            logger.warning('No experiment or models available to set on the experiment.')
        pass

    def remove_experiment(self, index: int) -> None:
        """
        Remove the experiment at the given index.
        """
        total = len(self.available())
        if not (0 <= index < total):
            logger.warning('Experiment index %s is out of range.', index)
            return

        experiments = self._project_lib._experiments
        exp_key = self._experiment_key_at_index(index)
        if exp_key is None:
            logger.warning('Experiment index %s is out of range.', index)
            return

        if hasattr(experiments, 'items'):
            del experiments[exp_key]
        else:
            experiments.pop(index)

        current = self._project_lib._current_experiment_index
        new_total = max(0, total - 1)
        if new_total == 0:
            self._project_lib._current_experiment_index = 0
        elif current > index:
            self._project_lib._current_experiment_index = current - 1
        elif current >= new_total:
            self._project_lib._current_experiment_index = new_total - 1
