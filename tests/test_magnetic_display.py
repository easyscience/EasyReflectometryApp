"""Phase 5a/5b/5c: magnetic depth profiles and spin asymmetry in the plotting backend.

The regression that matters most here is the one at the top: a project without
magnetism and without polarized data must behave exactly as it did before.
"""

from pathlib import Path

import numpy as np
import pytest
from easyscience import global_object

from EasyReflectometryApp.Backends.Py.plotting_1d import Plotting1d

ROOT = Path(__file__).resolve().parents[1]


def _plain_project():
    from easyreflectometry import Project as RealProject

    global_object.map._clear()
    project = RealProject()
    project.calculator = 'refl1d'
    project.default_model()
    return project


def _magnetic_project(rho_m: float = 3.0, theta_m: float = 270.0):
    from easyreflectometry.sample import LayerMagnetism

    project = _plain_project()
    # The middle assembly is the only real layer of the default model.
    project.models[0].sample[1].layers[0].magnetism = LayerMagnetism(rho_m=rho_m, theta_m=theta_m)
    return project


def _polarized_project(tmp_path, magnetic: bool = False):
    """A project with one pp/mm experiment; optionally with a magnetic model."""
    project = _magnetic_project() if magnetic else _plain_project()
    q = np.linspace(0.01, 0.2, 25)
    paths = {}
    for channel, scale in (('pp', 1.2), ('mm', 0.8)):
        path = tmp_path / f'run_{channel}.dat'
        reflectivity = scale * np.exp(-q * 30)
        np.savetxt(path, np.column_stack([q, reflectivity, 0.001 * reflectivity]))
        paths[channel] = str(path)
    project.load_polarized_experiment(paths)
    return project


class TestNonMagneticProjectIsUnchanged:
    """The gate: nothing new appears for ordinary, unpolarized work."""

    def test_no_magnetic_curves_and_no_spin_asymmetry(self, qcore_application):
        plotting = Plotting1d(project_lib=_plain_project(), parent=None)

        assert plotting.anyModelHasMagnetism is False
        assert plotting.modelHasMagnetism(0) is False
        assert plotting.getMagneticSldDataPointsForModel(0, 'spin_up') == []
        assert plotting.spinAsymmetryAvailable is False
        assert plotting.getSpinAsymmetryPoints(0) == []
        assert plotting.getSpinAsymmetryCalculatedPoints(0) == []

    def test_sld_range_is_the_nuclear_range(self, qcore_application):
        project = _plain_project()
        plotting = Plotting1d(project_lib=project, parent=None)

        nuclear = project.sld_data_for_model_at_index(0)
        min_x, max_x, min_y, max_y = plotting._get_all_models_sld_range()

        assert (min_x, max_x) == (nuclear.x.min(), nuclear.x.max())
        assert (min_y, max_y) == (nuclear.y.min(), nuclear.y.max())


class TestMagneticSldCurves:
    def test_curves_are_available_for_a_magnetic_model(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        assert plotting.anyModelHasMagnetism is True
        assert plotting.modelHasMagnetism(0) is True
        for curve in ('spin_up', 'spin_down', 'rho_m', 'theta_m'):
            points = plotting.getMagneticSldDataPointsForModel(0, curve)
            assert len(points) > 0
            assert set(points[0]) == {'x', 'y'}

    def test_spin_potentials_straddle_the_nuclear_profile(self, qcore_application):
        project = _magnetic_project()
        plotting = Plotting1d(project_lib=project, parent=None)

        up = np.array([point['y'] for point in plotting.getMagneticSldDataPointsForModel(0, 'spin_up')])
        down = np.array([point['y'] for point in plotting.getMagneticSldDataPointsForModel(0, 'spin_down')])
        nuclear = project.sld_data_for_model_at_index(0).y

        assert up.max() > nuclear.max()
        assert down.min() < nuclear.min()

    def test_unknown_curve_is_rejected(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        assert plotting.getMagneticSldDataPointsForModel(0, 'nonsense') == []

    def test_visible_curves_default_and_toggle(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)
        emitted = {'count': 0}
        plotting.magneticProfileChanged.connect(lambda: emitted.__setitem__('count', emitted['count'] + 1))

        # The spin potentials are the default; rho_m/theta_m are opt-in.
        assert plotting.visibleSldCurves == ['spin_up', 'spin_down']
        assert plotting.sldCurveVisible('rho_m') is False

        plotting.setSldCurveVisible('rho_m', True)
        assert plotting.sldCurveVisible('rho_m') is True
        assert emitted['count'] == 1

        # The two potentials are one control: hiding one hides both.
        plotting.setSldCurveVisible('spin_down', False)
        assert plotting.visibleSldCurves == ['rho_m']

        plotting.setSldCurveVisible('spin_up', True)
        assert plotting.visibleSldCurves == ['spin_up', 'spin_down', 'rho_m']

    def test_unknown_curve_cannot_be_toggled(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        plotting.setSldCurveVisible('nonsense', True)

        assert plotting.visibleSldCurves == ['spin_up', 'spin_down']

    def test_sld_range_covers_the_visible_magnetic_curves(self, qcore_application):
        """rho + rhoM exceeds rho: without this the new curves are clipped."""
        project = _magnetic_project()
        plotting = Plotting1d(project_lib=project, parent=None)

        nuclear = project.sld_data_for_model_at_index(0)
        _, _, min_y, max_y = plotting._get_all_models_sld_range()

        assert max_y > nuclear.y.max()
        assert min_y < nuclear.y.min()

        # Hiding them again restores the nuclear-only range.
        plotting.setSldCurveVisible('spin_up', False)
        _, _, min_hidden, max_hidden = plotting._get_all_models_sld_range()
        assert (min_hidden, max_hidden) == (nuclear.y.min(), nuclear.y.max())

    def test_theta_axis_range(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(theta_m=200.0), parent=None)

        low, high = plotting.sldThetaMinY, plotting.sldThetaMaxY

        assert low <= 200.0 <= high
        assert high > low  # a collapsed axis would draw nothing


class TestSpinAsymmetry:
    def test_available_for_a_pp_mm_experiment(self, qcore_application, tmp_path):
        plotting = Plotting1d(project_lib=_polarized_project(tmp_path), parent=None)

        assert plotting.spinAsymmetryAvailable is True
        points = plotting.getSpinAsymmetryPoints(0)
        assert len(points) == 25
        assert set(points[0]) == {'x', 'y', 'errorUpper', 'errorLower'}
        # pp is 1.2x, mm 0.8x of the same curve: SA = 0.4/2.0 = 0.2 everywhere.
        assert all(abs(point['y'] - 0.2) < 1e-9 for point in points)
        assert points[0]['errorUpper'] > points[0]['y'] > points[0]['errorLower']

    def test_axis_range_follows_the_data(self, qcore_application, tmp_path):
        plotting = Plotting1d(project_lib=_polarized_project(tmp_path), parent=None)

        assert plotting.spinAsymmetryMinX == pytest.approx(0.01)
        assert plotting.spinAsymmetryMaxX == pytest.approx(0.2)
        assert -1.05 <= plotting.spinAsymmetryMinY <= plotting.spinAsymmetryMaxY <= 1.05

    def test_no_calculated_curve_without_a_magnetic_model(self, qcore_application, tmp_path):
        plotting = Plotting1d(project_lib=_polarized_project(tmp_path), parent=None)

        assert plotting.spinAsymmetryCalculatedAvailable is False
        assert plotting.getSpinAsymmetryCalculatedPoints(0) == []

    def test_calculated_curve_for_a_magnetic_model(self, qcore_application, tmp_path):
        plotting = Plotting1d(project_lib=_polarized_project(tmp_path, magnetic=True), parent=None)

        assert plotting.spinAsymmetryCalculatedAvailable is True
        calculated = plotting.getSpinAsymmetryCalculatedPoints(0)
        assert len(calculated) == len(plotting.getSpinAsymmetryPoints(0))
        # A magnetic model has a real asymmetry, not the flat zero of a
        # non-magnetic one.
        assert max(abs(point['y']) for point in calculated) > 1e-3

    def test_unpolarized_experiment_has_no_asymmetry(self, qcore_application, tmp_path):
        project = _plain_project()
        q = np.linspace(0.01, 0.2, 25)
        path = tmp_path / 'plain.dat'
        np.savetxt(path, np.column_stack([q, np.exp(-q * 30), 0.01 * np.exp(-q * 30)]))
        project.load_experiment_for_model_at_index(str(path), 0)
        plotting = Plotting1d(project_lib=project, parent=None)

        assert plotting.spinAsymmetryAvailable is False
        assert plotting.getSpinAsymmetryPoints(0) == []

    def test_result_is_cached_until_invalidated(self, qcore_application, tmp_path):
        plotting = Plotting1d(project_lib=_polarized_project(tmp_path), parent=None)

        first = plotting._spin_asymmetry(0)
        assert plotting._spin_asymmetry(0) is first

        plotting.notifySpinAsymmetryChanged()

        assert plotting._spin_asymmetry(0) is not first


class TestReviewFixes:
    """CR1_PHASE5 findings that are visible at the backend boundary."""

    def test_magnetic_profiles_are_cached_until_invalidated(self, qcore_application):
        """Mo3: each miss is a full refl1d profile evaluation."""
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        first = plotting._magnetic_sld_profiles(0)
        assert plotting._magnetic_sld_profiles(0) is first

        plotting.notifyMagneticProfileChanged()

        assert plotting._magnetic_sld_profiles(0) is not first

    def test_spin_asymmetry_axis_expands_beyond_the_default_window(self, qcore_application, tmp_path):
        """Mo2: background-subtracted data can legitimately exceed |SA| = 1."""
        from easyreflectometry.data import DataSet1D
        from easyreflectometry.data import PolarizedDataSet

        project = _plain_project()
        q = np.linspace(0.01, 0.2, 10)
        # R-- slightly negative after background subtraction: SA > 1.
        channels = {
            'pp': DataSet1D(name='pp', x=q, y=np.full_like(q, 1.0), ye=np.full_like(q, 1e-12)),
            'mm': DataSet1D(name='mm', x=q, y=np.full_like(q, -0.5), ye=np.full_like(q, 1e-12)),
        }
        project._experiments[0] = PolarizedDataSet(name='subtracted', channels=channels, model=project.models[0])
        plotting = Plotting1d(project_lib=project, parent=None)

        points = plotting.getSpinAsymmetryPoints(0)

        assert points, 'the points are significant and must be kept'
        assert points[0]['y'] == pytest.approx(3.0)
        # The axis follows them instead of cutting them off at 1.05.
        assert plotting.spinAsymmetryMaxY >= 3.0

    def test_ordinary_spin_asymmetry_keeps_the_full_default_window(self, qcore_application, tmp_path):
        plotting = Plotting1d(project_lib=_polarized_project(tmp_path), parent=None)

        assert plotting.spinAsymmetryMinY == pytest.approx(-1.05)
        assert plotting.spinAsymmetryMaxY == pytest.approx(1.05)

    def test_out_of_overlap_points_are_reported(self, qcore_application, tmp_path):
        """M2: channels that do not cover the same q must not be extrapolated."""
        from easyreflectometry.data import DataSet1D
        from easyreflectometry.data import PolarizedDataSet

        project = _plain_project()
        q_pp = np.linspace(0.01, 0.30, 30)
        q_mm = np.linspace(0.01, 0.20, 20)
        channels = {
            'pp': DataSet1D(name='pp', x=q_pp, y=np.full_like(q_pp, 0.6), ye=np.full_like(q_pp, 1e-12)),
            'mm': DataSet1D(name='mm', x=q_mm, y=np.full_like(q_mm, 0.2), ye=np.full_like(q_mm, 1e-12)),
        }
        project._experiments[0] = PolarizedDataSet(name='partial', channels=channels, model=project.models[0])
        plotting = Plotting1d(project_lib=project, parent=None)

        assert plotting.spinAsymmetryOutOfOverlapPoints > 0
        assert plotting.spinAsymmetryMaxX <= 0.20

    def test_theta_curve_is_restricted_to_the_magnetic_region(self, qcore_application):
        """m1: no moment, no meaningful angle."""
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        theta = plotting.getMagneticSldDataPointsForModel(0, 'theta_m')
        rho_m = plotting.getMagneticSldDataPointsForModel(0, 'rho_m')

        assert 0 < len(theta) < len(rho_m)


class TestCr2Fixes:
    """CR2_PHASE5 findings that are visible at the backend/QML-source boundary."""

    def test_theta_curve_comes_in_pieces_that_are_not_joined(self, qcore_application):
        """Two magnetic layers with a gap must not be joined across the spacer."""
        from easyreflectometry.model import Model
        from easyreflectometry.model import ModelCollection
        from easyreflectometry.model import PercentageFwhm
        from easyreflectometry.sample import Layer
        from easyreflectometry.sample import LayerMagnetism
        from easyreflectometry.sample import Material
        from easyreflectometry.sample import Multilayer
        from easyreflectometry.sample import Sample

        global_object.map._clear()
        from easyreflectometry import Project as RealProject

        vacuum = Material(sld=0, isld=0, name='Vacuum')
        iron = Material(sld=8.0, isld=0, name='Fe')
        spacer = Material(sld=4.0, isld=0, name='Spacer')
        si = Material(sld=2.047, isld=0, name='Si')
        layers = [
            Layer(material=vacuum, thickness=0, roughness=0, name='Vacuum Superphase'),
            Layer(material=iron, thickness=80, roughness=2, magnetism=LayerMagnetism(rho_m=4.0), name='Fe top'),
            Layer(material=spacer, thickness=120, roughness=2, name='Spacer'),
            Layer(material=iron, thickness=80, roughness=2, magnetism=LayerMagnetism(rho_m=4.0), name='Fe bottom'),
            Layer(material=si, thickness=0, roughness=2, name='Si Subphase'),
        ]
        sample = Sample(*[Multilayer(layer) for layer in layers], name='Multilayer')
        model = Model(sample=sample, scale=1, background=0, name='Two magnetic layers')
        model.resolution_function = PercentageFwhm(0)
        project = RealProject()
        project.calculator = 'refl1d'
        project.models = ModelCollection(model)
        plotting = Plotting1d(project_lib=project, parent=None)

        segments = plotting.getMagneticSldSegmentsForModel(0, 'theta_m')

        assert len(segments) == 2
        assert all(len(segment) > 0 for segment in segments)
        # The gap between the pieces is the non-magnetic spacer.
        assert segments[1][0]['x'] - segments[0][-1]['x'] > 50

    def test_continuous_curves_are_a_single_piece(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        for curve in ('spin_up', 'spin_down', 'rho_m'):
            assert len(plotting.getMagneticSldSegmentsForModel(0, curve)) == 1

    def test_segment_accessor_is_bounds_checked(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        assert plotting.getMagneticSldSegment(0, 'rho_m', 0)
        assert plotting.getMagneticSldSegment(0, 'rho_m', 7) == []
        assert plotting.getMagneticSldSegment(0, 'nonsense', 0) == []

    def test_sld_chart_applies_the_new_range_to_the_live_axis(self):
        """Enabling a curve must not leave it drawn outside the current axis."""
        chart = (ROOT / 'EasyReflectometryApp' / 'Gui' / 'SldChart.qml').read_text(encoding='utf-8')

        assert 'onVisibleMagneticCurvesChanged: Qt.callLater(rebuildAndFitAxis)' in chart
        assert 'function growAxisToVisibleRange()' in chart
        assert 'axisY.min = low' in chart and 'axisY.max = high' in chart

    def test_sld_chart_assigns_series_arrays_instead_of_mutating_them(self):
        """A push() into a `property var` does not notify the legend Repeater."""
        chart = (ROOT / 'EasyReflectometryApp' / 'Gui' / 'SldChart.qml').read_text(encoding='utf-8')

        assert 'magneticSeries = newMagneticSeries' in chart
        assert 'sldSeries = newSldSeries' in chart
        assert 'magneticSeries.push(' not in chart

    def test_spin_asymmetry_chart_names_the_envelope_honestly(self):
        chart = (ROOT / 'EasyReflectometryApp' / 'Gui' / 'SpinAsymmetryChart.qml').read_text(encoding='utf-8')

        assert 'Uncertainty envelope' in chart

    def test_non_magnetic_pages_keep_their_qml_gates(self):
        """The §5.6 promise, pinned in the QML sources the app has no harness for."""
        experiment_tabs = (
            ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Experiment' / 'MainContent' / 'ExperimentTabs.qml'
        ).read_text(encoding='utf-8')
        analysis_tabs = (
            ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Analysis' / 'MainContent' / 'SldView.qml'
        ).read_text(encoding='utf-8')
        magnetic_group = (
            ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Sample' / 'Sidebar' / 'Basic' / 'Groups'
            / 'MagneticProfile.qml'
        ).read_text(encoding='utf-8')

        # Experiment page: no tab strip and no height without spin asymmetry.
        assert 'visible: root.spinAsymmetryAvailable' in experiment_tabs
        assert 'Layout.preferredHeight: root.spinAsymmetryAvailable ? EaStyle.Sizes.toolButtonHeight : 0' in experiment_tabs
        assert 'currentIndex: root.spinAsymmetryAvailable ? tabBar.currentIndex : 0' in experiment_tabs
        # Analysis page: the third tab is absent and never stays selected.
        assert 'visible: root.spinAsymmetryAvailable' in analysis_tabs
        assert 'tabBar.currentIndex = 0' in analysis_tabs
        # Sample page: the magnetic controls do not exist without magnetism.
        assert 'visible: Globals.BackendWrapper.plottingAnyModelHasMagnetism' in magnetic_group

    def test_series_signature_tracks_the_number_of_pieces(self):
        """A moment going to zero changes the piece count, not the curve set."""
        chart = (ROOT / 'EasyReflectometryApp' / 'Gui' / 'SldChart.qml').read_text(encoding='utf-8')

        # The signature must include the piece count, or the chart only refills
        # and never creates/removes the series for a region that appeared or
        # disappeared.
        assert 'plottingGetMagneticSldSegmentsForModel(i, curves[c]).length' in chart
        assert "parts.push(i + ':' + curves[c] + ':' + pieces)" in chart


class TestCalculationEngineUx:
    """Enabling magnetism must not point at a page the user cannot reach."""

    def test_magnetism_group_offers_the_switch_instead_of_the_analysis_page(self):
        group = (
            ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Sample' / 'Sidebar' / 'Basic' / 'Groups'
            / 'Magnetism.qml'
        ).read_text(encoding='utf-8')

        # The old dead end pointed at a tab that is disabled until the user has
        # been through the Experiment page.
        assert 'Analysis page' not in group
        assert "Ticking 'Magn.' offers to switch this project to it" in group
        assert 'function onMagnetismNeedsEngine(index, engine)' in group
        assert 'sampleEnableMagnetismWithEngineAtIndex' in group
        # The checkbox follows the backend, since confirming happens later.
        assert 'checked = Qt.binding(function () {' in group

    def test_engine_selector_is_available_on_the_sample_page(self):
        layout = (
            ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Sample' / 'Sidebar' / 'Advanced' / 'Layout.qml'
        ).read_text(encoding='utf-8')
        group = (
            ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Sample' / 'Sidebar' / 'Advanced' / 'Groups'
            / 'CalculationEngine.qml'
        ).read_text(encoding='utf-8')
        analysis_group = (
            ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Analysis' / 'Sidebar' / 'Advanced' / 'Groups'
            / 'Calculator.qml'
        ).read_text(encoding='utf-8')

        assert 'Groups.CalculationEngine' in layout
        # Both pages drive the same control, so they cannot disagree.
        assert 'Gui.CalculationEngineControl' in group
        assert 'Gui.CalculationEngineControl' in analysis_group

    def test_engine_rejection_is_shown_in_a_dialog(self):
        """Logs are invisible in the GUI, so a refused switch must say why.

        The dialog lives in the application window: the engine selector is
        instantiated on two pages, and per-instance dialogs would stack.
        """
        window = (ROOT / 'EasyReflectometryApp' / 'Gui' / 'ApplicationWindow.qml').read_text(encoding='utf-8')
        control = (ROOT / 'EasyReflectometryApp' / 'Gui' / 'CalculationEngineControl.qml').read_text(encoding='utf-8')

        assert 'function onCalculationEngineRejected(message)' in window
        assert 'engineRejectionDialog.open()' in window
        assert 'onCalculationEngineRejected' not in control

    def test_profile_failure_is_shown_in_the_sidebar(self):
        """A magnetic model losing its curves must not be a silent debug log."""
        control = (ROOT / 'EasyReflectometryApp' / 'Gui' / 'MagneticProfileControl.qml').read_text(encoding='utf-8')
        wrapper = (ROOT / 'EasyReflectometryApp' / 'Gui' / 'Globals' / 'BackendWrapper.qml').read_text(encoding='utf-8')

        assert 'plottingMagneticProfileError' in control
        assert 'plottingMagneticProfileError' in wrapper

    def test_import_dialog_mentions_the_engine_limitation(self):
        dialog = (
            ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Experiment' / 'Sidebar' / 'Basic' / 'Popups'
            / 'PolarizedChannelAssignment.qml'
        ).read_text(encoding='utf-8')

        assert 'sampleCalculationEnginesSupportingMagnetism' in dialog
