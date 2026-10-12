"""Source-level assertions on the Structure tab QML (no QML engine is instantiated;
rendering is verified by running the app)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'EasyReflectometryApp' / 'Gui'


def test_sample_page_declares_structure_tab():
    layout_qml = (GUI / 'Pages' / 'Sample' / 'Layout.qml').read_text(encoding='utf-8')

    assert "EaElements.TabButton { text: qsTr('Structure') }" in layout_qml
    assert 'MainContent/StructureView.qml' in layout_qml


def test_structure_view_binds_to_backend_contract():
    view_qml = (GUI / 'Pages' / 'Sample' / 'MainContent' / 'StructureView.qml').read_text(encoding='utf-8')

    assert 'Globals.BackendWrapper.sampleStructure' in view_qml
    assert 'Globals.BackendWrapper.sampleStructureLegend' in view_qml
    assert 'Globals.BackendWrapper.sampleStructureTotalThickness' in view_qml
    # Click-to-select wiring
    assert 'sampleSetCurrentAssemblyIndex(modelData.assembly_index)' in view_qml
    assert 'sampleSetCurrentLayerIndex(modelData.layer_index)' in view_qml
    # Empty state and overflow handling
    assert "qsTr('No layers defined')" in view_qml
    assert 'Flickable' in view_qml


def test_backend_wrapper_and_mock_expose_structure_properties():
    wrapper_qml = (GUI / 'Globals' / 'BackendWrapper.qml').read_text(encoding='utf-8')
    mock_qml = (ROOT / 'EasyReflectometryApp' / 'Backends' / 'Mock' / 'Sample.qml').read_text(encoding='utf-8')

    for name in ('structure', 'structureLegend', 'structureTotalThickness'):
        assert f'activeBackend.sample.{name}' in wrapper_qml
        assert name in mock_qml
    # Mock must keep the numeric thickness convention (not the all-string layers style)
    assert "'thickness': 2.5" in mock_qml


def test_structure_view_draws_moment_arrows_only_for_magnetic_layers():
    view_qml = (GUI / 'Pages' / 'Sample' / 'MainContent' / 'StructureView.qml').read_text(encoding='utf-8')

    # The arrow zone (and therefore the three-column layout) exists only where
    # the backend marked the box magnetic; every other box is laid out as before.
    assert "modelData.magnetic === true ? Math.min(height, root.maxGlyphPx) : 0" in view_qml
    assert 'Gui.MagnetizationArrow {' in view_qml
    assert 'visible: box.showArrow' in view_qml
    assert 'phi: modelData.phi ?? 0' in view_qml
    assert 'hasMoment: modelData.has_moment === true' in view_qml
    # The name column yields to the arrow; the thickness column is untouched.
    assert 'x: box.showArrow ? box.gap : (box.width - width) / 2' in view_qml
    assert 'width: Math.min(implicitWidth, box.nameWidthLimit)' in view_qml


def test_guide_field_legend_is_gated_on_a_magnetic_box():
    view_qml = (GUI / 'Pages' / 'Sample' / 'MainContent' / 'StructureView.qml').read_text(encoding='utf-8')

    assert 'Gui.GuideFieldLegend {' in view_qml
    assert 'visible: root.anyBoxMagnetic' in view_qml
    assert 'boxes.some(box => box.magnetic === true)' in view_qml


def test_magnetic_tooltip_leads_with_the_angle_the_arrow_draws():
    view_qml = (GUI / 'Pages' / 'Sample' / 'MainContent' / 'StructureView.qml').read_text(encoding='utf-8')

    assert "qsTr('Moment: %1° from H (θM %2°, ρM %3)')" in view_qml
    assert "qsTr('Magnetic, no moment (ρM %1)')" in view_qml
    assert 'M∥ %1 (no spin flip), M⊥ %2 (spin flip)' in view_qml
