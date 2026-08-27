"""Model spin cross-sections on the sample page reflectivity chart.

The SLD chart splits a magnetic model into rho-up/rho-down; the reflectivity
chart next to it drew a single curve. That curve is not an unpolarized average:
with magnetism enabled the calculator returns the cross-section of its current
polarization channel ('pp'). These tests pin both halves of that — the split
being available, and the plain curve being the up-up cross-section.

As in test_magnetic_display.py, the regression that matters most is the first
one: a project without magnetism must behave exactly as it did before.
"""

from pathlib import Path

import numpy as np
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


def _y_values(points: list) -> np.ndarray:
    return np.array([point['y'] for point in points])


class TestNonMagneticProjectIsUnchanged:
    def test_no_cross_sections_are_drawn(self, qcore_application):
        plotting = Plotting1d(project_lib=_plain_project(), parent=None)

        assert plotting.showModelChannels is False
        assert plotting.getSampleChannelDataPointsForModel(0, 'pp') == []

    def test_asking_for_them_anyway_draws_nothing(self, qcore_application):
        """The control is hidden without magnetism; the backend must agree."""
        plotting = Plotting1d(project_lib=_plain_project(), parent=None)

        plotting.setShowModelChannels(True)

        assert plotting.getSampleChannelDataPointsForModel(0, 'mm') == []

    def test_sample_range_is_the_plain_range(self, qcore_application):
        project = _plain_project()
        plotting = Plotting1d(project_lib=project, parent=None)

        plain = project.sample_data_for_model_at_index(0)
        min_x, max_x, _, max_y = plotting._get_all_models_sample_range()

        assert (min_x, max_x) == (plain.x.min(), plain.x.max())
        assert max_y == np.log10(plain.y[plain.y > 0].max())


class TestCrossSectionsOfAMagneticModel:
    def test_the_plain_curve_is_the_up_up_cross_section(self, qcore_application):
        """Why the split is worth showing: today's single curve is R↑↑.

        If this ever fails the calculator's polarization channel has moved, and
        the note in the Magnetic profile group is wrong.
        """
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        plain = _y_values(plotting.getSampleDataPointsForModel(0))
        up_up = _y_values(plotting.getSampleChannelDataPointsForModel(0, 'pp'))

        assert up_up.size == plain.size
        assert np.array_equal(up_up, plain)

    def test_down_down_departs_from_it(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        plain = _y_values(plotting.getSampleDataPointsForModel(0))
        down_down = _y_values(plotting.getSampleChannelDataPointsForModel(0, 'mm'))

        assert down_down.size == plain.size
        assert not np.allclose(down_down, plain)

    def test_the_curves_are_drawn_without_resolution_smearing(self, qcore_application):
        """The plain curve is ideal; a smeared cross-section next to it would
        compare the model against itself under two different instruments."""
        from easyreflectometry.model import PercentageFwhm

        project = _magnetic_project()
        project.models[0].resolution_function = PercentageFwhm(5.0)
        plotting = Plotting1d(project_lib=project, parent=None)

        up_up = _y_values(plotting.getSampleChannelDataPointsForModel(0, 'pp'))
        plain = _y_values(plotting.getSampleDataPointsForModel(0))

        assert np.array_equal(up_up, plain)
        # ... and the model keeps the resolution it came with.
        assert project.models[0].resolution_function.as_dict()['constant'] == 5.0

    def test_points_follow_the_rq4_plot_mode(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        plain_mode = _y_values(plotting.getSampleChannelDataPointsForModel(0, 'mm'))
        plotting._plot_rq4 = True
        plotting._model_channel_cache = {}
        rq4_mode = _y_values(plotting.getSampleChannelDataPointsForModel(0, 'mm'))

        assert not np.allclose(plain_mode, rq4_mode)

    def test_unknown_channel_is_rejected(self, qcore_application):
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)

        assert plotting.getSampleChannelDataPointsForModel(0, 'nonsense') == []

    def test_the_split_is_off_until_asked_for(self, qcore_application):
        """R↓↓ genuinely departs from R↑↑, so the headline chart of an existing
        project is not silently changed."""
        plotting = Plotting1d(project_lib=_magnetic_project(), parent=None)
        emitted = {'count': 0}
        plotting.magneticProfileChanged.connect(lambda: emitted.__setitem__('count', emitted['count'] + 1))

        assert plotting.showModelChannels is False

        plotting.setShowModelChannels(True)
        assert plotting.showModelChannels is True
        assert emitted['count'] == 1

        # A repeated toggle changes nothing, so it must not redraw either.
        plotting.setShowModelChannels(True)
        assert emitted['count'] == 1

    def test_a_parameter_change_recomputes_the_curves(self, qcore_application):
        project = _magnetic_project(rho_m=3.0)
        plotting = Plotting1d(project_lib=project, parent=None)
        plotting.setShowModelChannels(True)

        before = _y_values(plotting.getSampleChannelDataPointsForModel(0, 'mm'))
        project.models[0].sample[1].layers[0].magnetism.rho_m.value = 1.0
        plotting.refreshSamplePage()
        after = _y_values(plotting.getSampleChannelDataPointsForModel(0, 'mm'))

        assert not np.allclose(before, after)


class TestGuiWiring:
    """The control is only useful if it reaches the charts."""

    def test_the_switch_sits_with_the_magnetic_profile_ones(self):
        group = (
            ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Sample' / 'Sidebar' / 'Basic' / 'Groups'
            / 'MagneticProfile.qml'
        ).read_text(encoding='utf-8')

        assert 'plottingSetShowModelChannels' in group
        # Hidden entirely until a layer is magnetic, like the SLD controls.
        assert 'plottingAnyModelHasMagnetism' in group

    def test_both_sample_charts_draw_the_cross_sections(self):
        """The sample page has two reflectivity views; neither may be missed."""
        main_content = ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Sample' / 'MainContent'
        for name in ('SampleView.qml', 'CombinedView.qml'):
            view = (main_content / name).read_text(encoding='utf-8')
            assert 'ChannelCurves.js' in view, name
            assert 'ChannelCurves.create' in view, name
            assert 'ChannelCurves.refresh' in view, name
            # Toggling the split must rebuild the series, not just refill them.
            assert 'function onMagneticProfileChanged' in view, name
