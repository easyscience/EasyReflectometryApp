"""Source-level assertions on the moment compass in the Magnetism group
(spin-direction design A5/A6). No QML engine is instantiated; the angle
convention itself is pinned in the library and in `test_logic_layers.py`.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'EasyReflectometryApp' / 'Gui'
COMPASS = GUI / 'MagnetizationCompass.qml'
GROUP = GUI / 'Pages' / 'Sample' / 'Sidebar' / 'Basic' / 'Groups' / 'Magnetism.qml'


def test_the_compass_reuses_the_shared_arrow():
    compass_qml = COMPASS.read_text(encoding='utf-8')

    assert 'MagnetizationArrow {' in compass_qml
    assert 'phi: root.phi' in compass_qml
    assert 'import QtQuick.Shapes' not in compass_qml


def test_the_compass_follows_the_selection_the_table_already_writes():
    group_qml = GROUP.read_text(encoding='utf-8')

    assert 'Globals.BackendWrapper.sampleLayersMagnetism[Globals.BackendWrapper.sampleCurrentLayerIndex]' in group_qml
    assert 'Gui.MagnetizationCompass {' in group_qml
    # Gone entirely - not just greyed out - for a layer with no magnetism.
    assert 'visible: magnetismGroup.currentRow !== null && magnetismGroup.currentRow.magnetic === "True"' in group_qml
    assert 'height: visible ? implicitHeight : 0' in group_qml


def test_the_rim_teaches_the_theta_m_convention():
    compass_qml = COMPASS.read_text(encoding='utf-8')

    # 270 at the guide field, growing clockwise on screen.
    assert "{theta: '270', dx: 1, dy: 0}" in compass_qml
    assert "{theta: '0', dx: 0, dy: -1}" in compass_qml
    assert "{theta: '90', dx: -1, dy: 0}" in compass_qml
    assert "{theta: '180', dx: 0, dy: 1}" in compass_qml
    assert 'text: "H"' in compass_qml


def test_dragging_asks_for_a_snapped_phi_and_never_computes_theta_m():
    compass_qml = COMPASS.read_text(encoding='utf-8')

    assert 'signal phiRequested(real phi)' in compass_qml
    assert 'property int snapDegrees: 5' in compass_qml
    assert 'Math.round(degrees / snapDegrees) * snapDegrees' in compass_qml
    # Converting a direction back into the parameter is the backend's job.
    assert '270' not in compass_qml.split('function requestFrom', 1)[1]


def test_the_group_writes_through_the_backend_and_refuses_when_it_must_not():
    group_qml = GROUP.read_text(encoding='utf-8')

    assert 'sampleSetLayerPhiAtIndex' in group_qml
    assert 'magnetismGroup.currentRow.editable === "True"' in group_qml
    assert '!Globals.BackendWrapper.analysisFittingRunning' in group_qml


def test_the_backend_contract_is_mirrored_in_the_wrapper_and_the_mock():
    wrapper = (GUI / 'Globals' / 'BackendWrapper.qml').read_text(encoding='utf-8')
    mock = (ROOT / 'EasyReflectometryApp' / 'Backends' / 'Mock' / 'Sample.qml').read_text(encoding='utf-8')

    assert 'sampleSetLayerPhiAtIndex' in wrapper
    assert 'function setLayerPhiAtIndex(index, value)' in mock
    assert "'phi': '130.0'" in mock
    assert "'editable': 'True'" in mock
