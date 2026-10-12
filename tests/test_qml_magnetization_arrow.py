"""Source-level assertions on the shared arrow components (no QML engine is
instantiated; rendering is verified by running the app).

The physics convention itself - which phi an angle maps to - is pinned in the
library (`tests/test_magnetic_markers.py` there, all four cardinals plus the
canted example). What can go wrong *here* is the screen mapping: phi is
counterclockwise, Qt rotates clockwise and Canvas's y points down, so applying
both corrections silently mirrors every arrow. The contract that rules that out
is "one negation on the item, no trigonometry in the paint code", and that is
what these tests hold to.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'EasyReflectometryApp' / 'Gui'
ARROW = GUI / 'MagnetizationArrow.qml'
LEGEND = GUI / 'GuideFieldLegend.qml'


def test_the_screen_mapping_is_a_single_negation_on_the_item():
    arrow_qml = ARROW.read_text(encoding='utf-8')

    assert 'rotation: -phi' in arrow_qml


def test_the_paint_code_carries_no_second_mapping():
    paint = ARROW.read_text(encoding='utf-8').split('onPaint:', 1)[1]

    # A sin/cos in the paint code would be the second half of the same
    # correction and would cancel the item rotation into a mirrored arrow.
    for banned in ('Math.sin', 'Math.cos', 'Math.atan', 'phi'):
        assert banned not in paint, f'{banned} in the paint code is a second angle mapping'
    # ... except for the hollow "no moment" dot, which is a circle, not a direction.
    assert 'ctx.arc(' in paint


def test_arrows_are_drawn_with_canvas_because_shapes_is_not_packaged():
    arrow_qml = ARROW.read_text(encoding='utf-8')

    assert 'Canvas {' in arrow_qml
    assert 'import QtQuick.Shapes' not in arrow_qml
    assert 'ShapePath' not in arrow_qml


def test_the_arrow_repaints_when_its_inputs_change():
    arrow_qml = ARROW.read_text(encoding='utf-8')

    for handler in ('onPhiChanged', 'onHasMomentChanged', 'onColorChanged'):
        assert f'{handler}: canvas.requestPaint()' in arrow_qml


def test_a_negligible_moment_draws_a_dot_rather_than_a_direction():
    arrow_qml = ARROW.read_text(encoding='utf-8')

    assert 'property bool hasMoment: true' in arrow_qml
    assert 'if (!root.hasMoment)' in arrow_qml


def test_the_guide_field_legend_reuses_the_arrow_at_phi_zero():
    legend_qml = LEGEND.read_text(encoding='utf-8')

    assert 'MagnetizationArrow {' in legend_qml
    assert 'phi: 0' in legend_qml
    assert 'text: "H"' in legend_qml


def test_both_components_are_registered_in_the_gui_module():
    qmldir = (GUI / 'qmldir').read_text(encoding='utf-8')

    assert 'MagnetizationArrow MagnetizationArrow.qml' in qmldir
    assert 'GuideFieldLegend GuideFieldLegend.qml' in qmldir
