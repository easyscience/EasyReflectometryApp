from easyreflectometry import Project as ProjectLib


class Status:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._minimizers_logic = None

    def set_minimizers_logic(self, minimizers_logic):
        self._minimizers_logic = minimizers_logic

    @property
    def project(self):
        return self._project_lib._info['name']

    @property
    def minimizer(self):
        if self._minimizers_logic is not None:
            available = self._minimizers_logic.minimizers_available()
            idx = self._minimizers_logic.minimizer_current_index()
            if 0 <= idx < len(available):
                return available[idx]
        return self._project_lib.minimizer.name

    @property
    def calculator(self):
        return self._project_lib.calculator

    @property
    def experiments_count(self):
        return str(len(self._project_lib._experiments.keys()))
