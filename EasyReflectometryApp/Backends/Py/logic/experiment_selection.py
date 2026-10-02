ALL_CHANNELS = frozenset({'pp', 'pm', 'mp', 'mm'})


class ExperimentSelection:
    """What the charts show: the selected experiments and the visible spin channels.

    One instance is shared by the Analysis and Plotting backends (PyBackend creates it),
    so neither has to read the other's state. Analysis changes the experiment selection,
    Plotting changes the channels; whoever changes it emits the Qt signals.
    """

    def __init__(self, indices: list[int] | None = None, visible_channels=ALL_CHANNELS):
        self._indices: list[int] = list(indices or [])
        self._visible_channels = frozenset(visible_channels)

    @property
    def indices(self) -> list[int]:
        return list(self._indices)

    @property
    def is_multi(self) -> bool:
        return len(self._indices) > 1

    def set_indices(self, indices, available_count: int) -> bool:
        """Select `indices`, dropping those out of range. With nothing valid left and at least
        one experiment available, the first experiment is selected. Returns whether the
        selection changed."""
        valid = [index for index in indices if 0 <= index < available_count]
        if not valid and available_count > 0:
            valid = [0]
        if valid == self._indices:
            return False
        self._indices = valid
        return True

    def remove_index(self, removed: int, available_count: int) -> bool:
        """Follow the removal of experiment `removed`: drop it and shift the later ones down.
        `available_count` is the number of experiments left."""
        shifted = [index - 1 if index > removed else index for index in self._indices if index != removed]
        return self.set_indices(shifted, available_count)

    def prune(self, available_count: int) -> bool:
        """Drop indices that no longer exist (after experiments were removed elsewhere)."""
        return self.set_indices(self._indices, available_count)

    def reset(self, current_index: int, available_count: int) -> bool:
        """Select only `current_index`, for a newly loaded or reset project."""
        return self.set_indices([current_index], available_count)

    @property
    def visible_channels(self) -> frozenset:
        return self._visible_channels

    @visible_channels.setter
    def visible_channels(self, channels) -> None:
        self._visible_channels = frozenset(channels)
