"""State container for Bayesian DREAM hyper-parameters and posterior results."""

_VALID_INITIALIZERS = ('eps', 'cov', 'lhs', 'random')


class Bayesian:
    """Holds DREAM hyper-parameters and the last posterior result.

    This is purely a state container — execution is delegated to the worker.
    """

    DEFAULTS = dict(samples=10000, burn=2000, population=10, thin=1, initializer='eps')

    def __init__(self):
        self._samples: int = self.DEFAULTS['samples']
        self._burn: int = self.DEFAULTS['burn']
        self._population: int = self.DEFAULTS['population']
        self._thin: int = self.DEFAULTS['thin']
        self._initializer: str = self.DEFAULTS['initializer']
        self._posterior: dict | None = None
        # Phase 2 — cached rendered assets and diagnostics
        self.corner_plot_url: str = ''
        self.trace_plot_url: str = ''
        self.heatmap_plot_url: str = ''
        self.heatmap_data: dict | None = None
        self.diagnostics: dict = {}

    # ------------------------------------------------------------------
    # Hyper-parameters
    # ------------------------------------------------------------------

    @property
    def samples(self) -> int:
        return self._samples

    @samples.setter
    def samples(self, value: int) -> None:
        if value > 0:
            self._samples = value
        else:
            raise ValueError('samples must be a positive integer')

    @property
    def burn(self) -> int:
        return self._burn

    @burn.setter
    def burn(self, value: int) -> None:
        if value >= 0:
            self._burn = value
        else:
            raise ValueError('burn must be a non-negative integer')

    @property
    def population(self) -> int:
        return self._population

    @population.setter
    def population(self, value: int) -> None:
        if value > 0:
            self._population = value
        else:
            raise ValueError('population must be a positive integer')

    @property
    def thin(self) -> int:
        return self._thin

    @thin.setter
    def thin(self, value: int) -> None:
        if value > 0:
            self._thin = value
        else:
            raise ValueError('thin must be a positive integer')

    @property
    def initializer(self) -> str:
        return self._initializer

    @initializer.setter
    def initializer(self, value: str) -> None:
        if value in _VALID_INITIALIZERS:
            self._initializer = value
        else:
            raise ValueError(
                f'Unknown initializer {value!r}. Valid options: {_VALID_INITIALIZERS}'
            )

    # ------------------------------------------------------------------
    # Posterior result
    # ------------------------------------------------------------------

    @property
    def posterior(self) -> dict | None:
        return self._posterior

    @property
    def has_result(self) -> bool:
        return self._posterior is not None

    def clear(self) -> None:
        """Clear the stored posterior result and all rendered / computed assets."""
        self._posterior = None
        self.corner_plot_url = ''
        self.trace_plot_url = ''
        self.heatmap_plot_url = ''
        self.heatmap_data = None
        self.diagnostics = {}
