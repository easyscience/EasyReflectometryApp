"""Source-level assertions on the moment angle slider in the Magnetism group
(spin-direction design A5/A6). No QML engine is instantiated; the angle
convention itself is pinned in the library and in `test_logic_layers.py`.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'EasyReflectometryApp' / 'Gui'
SLIDER = GUI / 'MagnetizationAngleSlider.qml'
GROUP = GUI / 'Pages' / 'Sample' / 'Sidebar' / 'Basic' / 'Groups' / 'Magnetism.qml'


def test_the_slider_spans_the_whole_theta_m_range():
    slider_qml = SLIDER.read_text(encoding='utf-8')

    assert 'from: 0' in slider_qml
    assert 'to: 360' in slider_qml
    # The dial snapped the drag to 5 deg; stepSize alone would only snap the
    # keyboard and the wheel.
    assert 'property int snapDegrees: 5' in slider_qml
    assert 'stepSize: root.snapDegrees' in slider_qml
    assert 'snapMode: Slider.SnapAlways' in slider_qml


def test_the_slider_reuses_the_shared_arrow_and_guide_field_reference():
    slider_qml = SLIDER.read_text(encoding='utf-8')

    assert 'MagnetizationArrow {' in slider_qml
    assert 'phi: root.phi' in slider_qml
    # An arrow is never on screen without the reference it is measured from.
    assert 'GuideFieldLegend {' in slider_qml
    assert 'import QtQuick.Shapes' not in slider_qml


def test_the_slider_edits_theta_m_and_leaves_phi_to_the_backend():
    slider_qml = SLIDER.read_text(encoding='utf-8')

    assert 'signal thetaMRequested(real thetaM)' in slider_qml
    assert 'onMoved: root.thetaMRequested(value)' in slider_qml
    # phi is drawn, never written: deriving it here would put the guide field
    # convention in QML, where it is already wrong once.
    assert 'phiRequested' not in slider_qml
    assert '270' not in slider_qml.split('EaElements.Slider {', 1)[1]


def test_the_backend_stays_authoritative_after_a_drag():
    slider_qml = SLIDER.read_text(encoding='utf-8')

    # Dragging assigns `value` imperatively, so the model value is applied by a
    # Binding that stands aside while the handle is held: a refused write must
    # move the handle back rather than leave it where the drag left it.
    assert 'Binding {' in slider_qml
    assert 'property: "value"' in slider_qml
    assert 'value: root.thetaM' in slider_qml
    assert 'when: !slider.pressed' in slider_qml


def test_the_slider_follows_the_selection_the_table_already_writes():
    group_qml = GROUP.read_text(encoding='utf-8')

    assert 'Globals.BackendWrapper.sampleLayersMagnetism[Globals.BackendWrapper.sampleCurrentLayerIndex]' in group_qml
    assert 'Gui.MagnetizationAngleSlider {' in group_qml
    # Gone entirely - not just greyed out - for a layer with no magnetism.
    assert 'visible: magnetismGroup.currentRow !== null && magnetismGroup.currentRow.magnetic === "True"' in group_qml
    assert 'height: visible ? implicitHeight : 0' in group_qml


def test_the_group_writes_through_the_backend_and_refuses_when_it_must_not():
    group_qml = GROUP.read_text(encoding='utf-8')

    # The same call the theta_m column makes: one write path for one parameter.
    assert 'sampleSetLayerThetaMAtIndex' in group_qml
    assert 'magnetismGroup.currentRow.editable === "True"' in group_qml
    assert '!Globals.BackendWrapper.analysisFittingRunning' in group_qml


def test_the_backend_contract_is_mirrored_in_the_wrapper_and_the_mock():
    wrapper = (GUI / 'Globals' / 'BackendWrapper.qml').read_text(encoding='utf-8')
    mock = (ROOT / 'EasyReflectometryApp' / 'Backends' / 'Mock' / 'Sample.qml').read_text(encoding='utf-8')

    assert 'sampleSetLayerThetaMAtIndex' in wrapper
    assert 'function setLayerThetaMAtIndex(index, value)' in mock
    assert "'phi': '130.0'" in mock
    assert "'editable': 'True'" in mock


def test_the_dial_is_gone():
    assert not (GUI / 'MagnetizationCompass.qml').exists()
    assert 'MagnetizationCompass' not in (GUI / 'qmldir').read_text(encoding='utf-8')
