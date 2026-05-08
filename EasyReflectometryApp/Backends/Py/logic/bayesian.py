"""State container for Bayesian DREAM hyper-parameters and posterior results."""


class Bayesian:
    """Holds DREAM hyper-parameters and the last posterior result.

    This is purely a state container — execution is delegated to the worker.
    """

    DEFAULTS = dict(samples=10000, burn=2000, population=10, thin=1)

    def __init__(self):
        self._samples: int = self.DEFAULTS['samples']
        self._burn: int = self.DEFAULTS['burn']
        self._population: int = self.DEFAULTS['population']
        self._thin: int = self.DEFAULTS['thin']
        self._posterior: dict | None = None

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
        """Clear the stored posterior result."""
        self._posterior = None
