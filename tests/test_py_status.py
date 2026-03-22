from EasyReflectometryApp.Backends.Py import status as status_module


class StubStatusLogic:
    def __init__(self, _project_lib):
        self.project = 'Demo Project'
        self.experiments_count = '4'
        self.calculator = 'refnx'
        self.minimizer = 'LeastSquares'


class StubParametersLogic:
    def __init__(self, _project_lib):
        self.as_status_string = '2 free / 10 total'


def test_status_wrapper_delegates_to_logic(monkeypatch, qcore_application):
    monkeypatch.setattr(status_module, 'StatusLogic', StubStatusLogic)
    monkeypatch.setattr(status_module, 'ParametersLogic', StubParametersLogic)

    status = status_module.Status(project_lib=object())

    assert status.project == 'Demo Project'
    assert status.experimentsCount == '4'
    assert status.calculator == 'refnx'
    assert status.minimizer == 'LeastSquares'
    assert status.variables == '2 free / 10 total'


def test_status_wrapper_phase_count_is_none(monkeypatch, qcore_application):
    monkeypatch.setattr(status_module, 'StatusLogic', StubStatusLogic)
    monkeypatch.setattr(status_module, 'ParametersLogic', StubParametersLogic)

    status = status_module.Status(project_lib=object())

    assert status.phaseCount is None
