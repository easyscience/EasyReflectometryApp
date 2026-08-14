from EasyReflectometryApp.Backends.Py import experiment as experiment_module


class StubModelsLogic:
    def __init__(self, _project_lib):
        self.scaling_at_current_index = 1.5
        self.background_at_current_index = 0.02
        self.resolution_at_current_index = '2%' 
        self.index = 0
        self.set_scaling_result = True
        self.set_background_result = True
        self.set_resolution_result = True
        self.last_scaling = None
        self.last_background = None
        self.last_resolution = None

    def set_scaling_at_current_index(self, value):
        self.last_scaling = value
        return self.set_scaling_result

    def set_background_at_current_index(self, value):
        self.last_background = value
        return self.set_background_result

    def set_resolution_at_current_index(self, value):
        self.last_resolution = value
        return self.set_resolution_result


class StubProjectLogic:
    def __init__(self, _project_lib):
        self.experimental_data_at_current_index = True
        self.dataset_counts = {}
        self.loaded_all = []
        self.loaded_new = []
        self.loaded_polarized = []
        self.load_polarized_result = True

    def count_datasets_in_file(self, path):
        return self.dataset_counts.get(path, 1)

    def load_all_experiments_from_file(self, path):
        self.loaded_all.append(path)
        return (2, False)

    def load_new_experiment(self, path):
        self.loaded_new.append(path)

    def suggest_polarized_channel_assignment(self, paths):
        return {path: ('pp' if '_uu' in path else 'mm' if '_dd' in path else '') for path in paths}

    def load_polarized_experiment(self, channel_to_path):
        self.loaded_polarized.append(dict(channel_to_path))
        return self.load_polarized_result


def _build_experiment(monkeypatch):
    monkeypatch.setattr(experiment_module, 'ModelsLogic', StubModelsLogic)
    monkeypatch.setattr(experiment_module, 'ProjectLogic', StubProjectLogic)
    return experiment_module.Experiment(project_lib=object())


def test_experiment_properties_and_set_model_index(monkeypatch, qcore_application):
    experiment = _build_experiment(monkeypatch)

    assert experiment.scaling == 1.5
    assert experiment.background == 0.02
    assert experiment.resolution == '2%'
    assert experiment.experimentalData is True

    experiment.setModelIndex(3)
    assert experiment._model_logic.index == 3


def test_setters_emit_signals_only_when_logic_accepts_change(monkeypatch, qcore_application):
    experiment = _build_experiment(monkeypatch)
    changed = {'experiment': 0, 'external': 0}
    experiment.experimentChanged.connect(lambda: changed.__setitem__('experiment', changed['experiment'] + 1))
    experiment.externalExperimentChanged.connect(lambda: changed.__setitem__('external', changed['external'] + 1))

    experiment.setScaling(2.5)
    experiment.setBackground(0.1)
    experiment.setResolution('3.3')

    assert experiment._model_logic.last_scaling == 2.5
    assert experiment._model_logic.last_background == 0.1
    assert experiment._model_logic.last_resolution == '3.3'
    assert changed == {'experiment': 3, 'external': 3}

    experiment._model_logic.set_scaling_result = False
    experiment._model_logic.set_background_result = False
    experiment._model_logic.set_resolution_result = False
    experiment.setScaling(7.0)
    experiment.setBackground(5.0)
    experiment.setResolution('4.4')

    assert changed == {'experiment': 3, 'external': 3}


def test_load_routes_single_vs_multi_dataset_paths(monkeypatch, qcore_application):
    experiment = _build_experiment(monkeypatch)
    experiment._project_logic.dataset_counts = {'A': 2, 'B': 1}
    monkeypatch.setattr(experiment_module.IO, 'generalizePath', lambda path: path)

    changed = {'experiment': 0, 'external': 0}
    experiment.experimentChanged.connect(lambda: changed.__setitem__('experiment', changed['experiment'] + 1))
    experiment.externalExperimentChanged.connect(lambda: changed.__setitem__('external', changed['external'] + 1))

    experiment.load('A,B')

    assert experiment._project_logic.loaded_all == ['A']
    assert experiment._project_logic.loaded_new == ['B']
    assert changed == {'experiment': 2, 'external': 2}


def test_suggest_polarized_channels_returns_editable_rows(monkeypatch, qcore_application):
    experiment = _build_experiment(monkeypatch)
    monkeypatch.setattr(experiment_module.IO, 'generalizePath', lambda path: path)

    rows = experiment.suggestPolarizedChannels('data/run_uu.dat,data/run_dd.dat,data/run_x.dat')

    assert rows == [
        {'path': 'data/run_uu.dat', 'name': 'run_uu.dat', 'channel': 'pp'},
        {'path': 'data/run_dd.dat', 'name': 'run_dd.dat', 'channel': 'mm'},
        {'path': 'data/run_x.dat', 'name': 'run_x.dat', 'channel': ''},
    ]


def test_load_polarized_builds_channel_mapping_and_emits(monkeypatch, qcore_application):
    experiment = _build_experiment(monkeypatch)
    changed = {'experiment': 0, 'external': 0, 'q_range': 0}
    experiment.experimentChanged.connect(lambda: changed.__setitem__('experiment', changed['experiment'] + 1))
    experiment.externalExperimentChanged.connect(lambda: changed.__setitem__('external', changed['external'] + 1))
    experiment.qRangeUpdated.connect(lambda: changed.__setitem__('q_range', changed['q_range'] + 1))

    experiment.loadPolarized(
        [
            {'path': 'run_uu.dat', 'channel': 'pp'},
            {'path': 'run_dd.dat', 'channel': 'mm'},
            {'path': 'run_x.dat', 'channel': ''},  # unassigned rows are skipped
        ]
    )

    assert experiment._project_logic.loaded_polarized == [{'pp': 'run_uu.dat', 'mm': 'run_dd.dat'}]
    assert changed == {'experiment': 1, 'external': 1, 'q_range': 1}


def test_polarized_slots_accept_qjsvalues_from_qml(monkeypatch, qcore_application):
    # QML hands over JS arrays/objects as QJSValue, not Python lists/dicts.
    from PySide6.QtQml import QJSEngine

    experiment = _build_experiment(monkeypatch)
    monkeypatch.setattr(experiment_module.IO, 'generalizePath', lambda path: path)
    engine = QJSEngine()

    paths = engine.evaluate("(['data/run_uu.dat', 'data/run_dd.dat'])")
    rows = experiment.suggestPolarizedChannels(paths)
    assert [row['channel'] for row in rows] == ['pp', 'mm']

    assignments = engine.evaluate(
        "([{path: 'run_uu.dat', channel: 'pp'}, {path: 'run_dd.dat', channel: 'mm'}])"
    )
    experiment.loadPolarized(assignments)
    assert experiment._project_logic.loaded_polarized == [{'pp': 'run_uu.dat', 'mm': 'run_dd.dat'}]


def test_load_polarized_without_assignments_is_a_no_op(monkeypatch, qcore_application):
    experiment = _build_experiment(monkeypatch)
    changed = {'count': 0}
    experiment.experimentChanged.connect(lambda: changed.__setitem__('count', changed['count'] + 1))

    experiment.loadPolarized([{'path': 'run_x.dat', 'channel': ''}])

    assert experiment._project_logic.loaded_polarized == []
    assert changed == {'count': 0}
