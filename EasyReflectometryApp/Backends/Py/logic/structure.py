from easyreflectometry import Project as ProjectLib
from easyreflectometry.model.model import COLORS

# An assembly whose expanded box count would exceed this collapses to its repeat unit
MAX_EXPANDED_BOXES_PER_ASSEMBLY = 12


def flatten(project_lib: ProjectLib) -> tuple[list[dict], list[dict], float]:
    """Flatten the current model's sample into drawable boxes for the Structure view.

    Returns (structure, legend, total_thickness):
    - structure: one dict per drawn box, top to bottom, with the keys
        label            layer name, or assembly name for a gradient
        material         material name, or 'front -> back' for a gradient
        color            box color; color_end is the second color of a gradient, else ''
        sld, isld        real/imaginary SLD of the material, preformatted to 2 decimals
        thickness        layer thickness in Angstrom, as a float
        roughness        upper roughness in Angstrom, preformatted to 1 decimal
        assembly         assembly name, and assembly_index/layer_index to address the layer
        kind             'layer' | 'gradient' | 'superphase' | 'subphase'
        repetitions      n for a collapsed repeating multilayer, else 1
    - legend: distinct {label, color} pairs in stack order
    - total_thickness: physical total in Angstrom (collapsed repeats counted n times, caps excluded)
    """
    model_index = project_lib.current_model_index
    if model_index is None or not 0 <= model_index < len(project_lib._models):
        return [], [], 0.0
    sample = project_lib._models[model_index].sample

    colors = _ColorMap(project_lib._materials)
    boxes = []
    total_thickness = 0.0

    for assembly_index, assembly in enumerate(sample):
        if assembly.type == 'Gradient-layer':
            boxes.append(_gradient_box(assembly, assembly_index, colors))
            total_thickness += boxes[-1]['thickness']
            continue

        repetitions = 1
        if assembly.type == 'Repeating Multi-layer':
            repetitions = int(assembly.repetitions.value)
        collapsed = repetitions * len(assembly.layers) > MAX_EXPANDED_BOXES_PER_ASSEMBLY
        total_thickness += repetitions * sum(layer.thickness.value for layer in assembly.layers)

        for _ in range(1 if collapsed else repetitions):
            for layer_index, layer in enumerate(assembly.layers):
                boxes.append(_layer_box(layer, assembly, assembly_index, layer_index, colors))
        if collapsed:
            boxes[-len(assembly.layers)]['repetitions'] = repetitions

    # The first/last drawn layers are the semi-infinite superphase/subphase caps and are
    # excluded from the total. Only a plain layer is retagged: a gradient assembly at either
    # end keeps its own kind (and its thickness), and a lone box is a superphase only.
    if boxes:
        for box, kind in ((boxes[0], 'superphase'), (boxes[-1], 'subphase')):
            if box['kind'] == 'layer':
                box['kind'] = kind
                total_thickness -= box['thickness']

    legend = []
    seen = set()
    for box in boxes:
        if box['material'] not in seen:
            seen.add(box['material'])
            legend.append({'label': box['material'], 'color': box['color']})

    return boxes, legend, total_thickness


def _value(quantity) -> float:
    # Material.sld is a Parameter, but MaterialSolvated.sld is a computed plain float
    return float(getattr(quantity, 'value', quantity))


def _layer_box(layer, assembly, assembly_index: int, layer_index: int, colors: '_ColorMap') -> dict:
    material = layer.material
    return {
        'label': layer.name,
        'material': material.name,
        'color': colors.get(material),
        'color_end': '',
        'sld': f'{_value(material.sld):.2f}',
        'isld': f'{_value(material.isld):.2f}',
        'thickness': float(layer.thickness.value),
        'roughness': f'{layer.roughness.value:.1f}',
        'assembly': assembly.name,
        'assembly_index': assembly_index,
        'layer_index': layer_index,
        'kind': 'layer',
        'repetitions': 1,
    }


def _gradient_box(assembly, assembly_index: int, colors: '_ColorMap') -> dict:
    # A gradient assembly is drawn as one box colored front->back; its internal
    # discretization slices use anonymous materials and are never drawn.
    front = assembly.front_material
    back = assembly.back_material
    return {
        'label': assembly.name,
        'material': f'{front.name} → {back.name}',
        'color': colors.get(front),
        'color_end': colors.get(back),
        'sld': f'{_value(front.sld):.2f}',
        'isld': f'{_value(front.isld):.2f}',
        'thickness': float(assembly.thickness),
        'roughness': f'{assembly.front_layer.roughness.value:.1f}',
        'assembly': assembly.name,
        'assembly_index': assembly_index,
        'layer_index': 0,
        'kind': 'gradient',
        'repetitions': 1,
    }


class _ColorMap:
    """Material name -> palette color; project materials by table position,
    unknown (ad-hoc) materials by first-seen order. Solvated materials are
    keyed on their inner dry material so the solvent does not change the color."""

    def __init__(self, materials):
        self._by_name = {material.name: COLORS[i % len(COLORS)] for i, material in enumerate(materials)}
        self._next_index = len(materials)

    def get(self, material) -> str:
        name = getattr(material, 'material', material).name
        if name not in self._by_name:
            self._by_name[name] = COLORS[self._next_index % len(COLORS)]
            self._next_index += 1
        return self._by_name[name]
