from easyreflectometry import Project as ProjectLib


class Calculators:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._list_available_calculators = self._project_lib._calculator.available_interfaces

    def available(self) -> list[str]:
        return self._list_available_calculators

    def current_index(self) -> int:
        """Position of the project's active calculator in the list.

        Derived rather than cached: the engine also changes when a project is
        loaded, or when enabling magnetism switches it from the Sample page, and
        a cached index would then show the wrong engine.
        """
        return self.index_of(self._project_lib.calculator)

    def index_of(self, name: str) -> int:
        """Position of a calculator in the list (-1 when it is not available).

        0 is a real engine (typically refnx), so it must not stand in for
        "not found" — callers rely on a negative result to detect a missing
        engine (see `enableMagnetismWithEngineAtIndex`).
        """
        if name in self._list_available_calculators:
            return self._list_available_calculators.index(name)
        return -1

    def supporting_magnetism(self) -> list[str]:
        """Available calculators that can model magnetic layers."""
        return list(self._project_lib.calculators_supporting_magnetism)

    def set_current_index(self, new_value: int) -> bool:
        if not 0 <= new_value < len(self._list_available_calculators):
            return False
        new_calculator = self._list_available_calculators[new_value]
        if new_calculator == self._project_lib.calculator:
            return False
        self._reject_if_magnetism_would_break(new_calculator)
        self._project_lib.calculator = new_calculator
        return True

    def _reject_if_magnetism_would_break(self, new_calculator: str) -> None:
        """Refuse a calculator that cannot carry the sample's magnetism.

        Binding a magnetic layer to such a calculator raises deep inside the
        library, and doing that from a QML-invoked slot takes the application
        down instead of reporting anything.
        """
        if not self._project_lib.models_have_magnetism:
            return
        if new_calculator in self._project_lib.calculators_supporting_magnetism:
            return
        raise NotImplementedError(
            f'The {new_calculator} calculation engine cannot model magnetic layers, and this sample has '
            'some. Remove the magnetism from the sample first (Sample page, Magnetism group).'
        )
