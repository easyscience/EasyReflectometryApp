pragma Singleton

import QtQuick

QtObject {
    // Signals to match the Python backend
    signal constraintsChanged
    // MATERIALS
    readonly property int currentMaterialIndex: -1

    // Getters
    readonly property var materials: [
        {
            'label': 'label 1',
            'sld': '1.23456',
            'isld': '-1.23456'
        },
        {
            'label': 'label 2',
            'sld': '2.34567',
            'isld': '-2.34567'
        },
        {
            'label': 'label 3',
            'sld': '3.45678',
            'isld': '-3.45678'
        },
    ]
    readonly property var materialNames: materials.map(function (item) { return item.label })

    // Setters
    function setCurrentMaterialIndex(value) {
        console.debug(`setCurrentMaterialIndex ${value}`)
    }
    function setCurrentMaterialName(value) {
        console.debug(`setCurrentMaterialName ${value}`)
    }
    function setCurrentMaterialSld(value) {
        console.debug(`setCurrentMaterialSld ${value}`)
    }
    function setCurrentMaterialISld(value) {
        console.debug(`setCurrentMaterialISld ${value}`)
    }


    // Table functions
    function removeMaterial(value) {
        console.debug(`removeMaterial ${value}`)
    }
    function addNewMaterial() {
        console.debug(`addNewMaterial`)
    }
    function duplicateSelectedMaterial() {
        console.debug(`duplicateSelectedMaterial ${currentMaterialIndex}`)
    }
    function moveSelectedMaterialUp() {
        console.debug(`moveSelectedMaterialUp ${currentMaterialIndex}`)
    }
    function moveSelectedMaterialDown() {
        console.debug(`moveSelectedMaterialDown ${currentMaterialIndex}`)
    }
    // MODELS
    property int currentModelIndex: -1
    property string currentModelName: 'currentModelName'

    // Getters
    readonly property var models: [
        {
            'label': 'label 1',
            'color': 'red',
        },
        {
            'label': 'label 2',
            'color': 'green'
        },
        {
            'label': 'label 3',
            'color': 'blue'
        },
    ]

    // Setters
    function setCurrentModelIndex(value){
        console.debug(`setCurrentModelIndex ${value}`)
    }
    function setCurrentModelName(value) {
        console.debug(`setCurrentModelName ${value}`)
    }

    // Table functions
    function removeModel(value) {
        console.debug(`removeModel ${value}`)
    }
    function addNewModel() {
        console.debug(`addNewModel`)
    }
    function duplicateSelectedModel() {
        console.debug(`duplicateSelectedModel ${currentModelIndex}`)
    }
    function moveSelectedModelUp() {
        console.debug(`moveSelectedModelUp ${currentModelIndex}`)
    }
    function moveSelectedModelDown() {
        console.debug(`moveSelectedModelDown ${currentModelIndex}`)
    }

    // ASSEMBLIES
    property int currentAssemblyIndex: -1
    property bool constrainAPM: false
    property bool conformalRoughness: false
    property int repeatedLayerReptitions: 1

    property string currentAssemblyName: 'currentAssemblyName'
    property string currentAssemblyType: 'Surfactant Layer'


    // Getters
    readonly property var assemblies: [
        {
            'label': 'label 1',
            'type': 'Multi-layer'
        },
        {
            'label': 'label 2',
            'type': 'Multi-layer'
        },
        {
            'label': 'label 3',
            'type': 'Repeating Multi-layer'

        },
        {
            'label': 'label 4',
            'type': 'Surfactant Layer'
        },
    ]

    // Setters
    function setCurrentAssemblyName(value) {
        console.debug(`setCurrentAssemblyName ${value}`)
    }
    function setCurrentAssemblyType(value) {
        console.debug(`setCurrentAssemblyType ${value}`)
    }
    function setCurrentAssemblyIndex(value) {
        currentAssemblyType = assemblies[value].type
        console.debug(`setCurrentAssemblyIndex ${value}`)
    }

    // Table functions
    function removeAssembly(value) {
        console.debug(`removeAssembly ${value}`)
    }
    function addNewAssembly() {
        console.debug(`addNewAssembly`)
    }
    function duplicateSelectedAssembly() {
        console.debug(`duplicateSelectedAssembly ${currentAssemblyIndex}`)
    }
    function moveSelectedAssemblyUp() {
        console.debug(`moveSelectedAssemblyUp ${currentAssemblyIndex}`)
    }
    function moveSelectedAssemblyDown() {
        console.debug(`moveSelectedAssemblyDown ${currentAssemblyIndex}`)
    }

    // Assembly specific
    property int currentAssemblyRepeatedLayerReptitions: 3

    function setCurrentAssemblyRepeatedLayerReptitions(value) {
        console.debug(`setCurrentAssemblyRepeatedLayerReptitions ${value}`)
    }

    function setCurrentAssemblyConstrainAPM(value) {
        console.debug(`setCurrentAssemblyConstrainAPM ${value}`)
    }

    function setCurrentAssemblyConformalRoughness(value) {
        console.debug(`setCurrentAssemblyConformalRoughness ${value}`)
    }

    // LAYERS
    property int currentLayerIndex: -1

    property string currentLayerName: 'currentLayerName'

    // Getters
    readonly property var layers: [
        {
            'formula': 'formula 1',
            'material': 'label 1',
            'solvent': 'label 1',
            'thickness': '1',
            'thickness_enabled': 'True',
            'roughness': '1',
            'roughness_enabled': 'True',
            'solvation': '1',
            'apm': '1',
            'apm_enabled': 'True',
        },
        {
            'formula': 'formula 2',
            'material': 'label 2',
            'solvent': 'label 2',
            'thickness': ' 2',
            'thickness_enabled': 'False',
            'roughness': '2',
            'roughness_enabled': 'False',
            'solvation': '2',
            'apm': '2',
            'apm_enabled': 'False',
        },
        {
            'formula': 'formula 3',
            'material': 'label 3',
            'solvent': 'label 3',
            'thickness': '3',
            'thickness_enabled': 'False',
            'roughness': '3',
            'roughness_enabled': 'False',
            'solvation': '3',
            'apm': '3',
            'apm_enabled': 'False',
        },
    ]

    // Setters
    function setCurrentLayerIndex(value){
        console.debug(`setCurrentLayerIndex ${value}`)
    }
    function setCurrentLayerFormula(value) {
        console.debug(`setCurrentLayerFormula ${value}`)
    }
    function setCurrentLayerMaterial(value) {
        console.debug(`setCurrentLayerMaterialIndex ${value}`)
    }
    function setCurrentLayerSolvent(value) {
        console.debug(`setCurrentLayerSolvent ${value}`)
    }
    function setCurrentLayerThickness(value) {
        console.debug(`setCurrentLayerThickness ${value}`)
    }
    function setCurrentLayerRoughness(value) {
        console.debug(`setCurrentLayerRoughness ${value}`)
    }
    function setCurrentLayerAPM(value) {
        console.debug(`setCurrentLayerAPM ${value}`)
    }
    function setCurrentLayerSolvation(value) {
        console.debug(`setCurrentLayerSolvation ${value}`)
    }

    // Table functions
    function removeLayer(value) {
        console.debug(`removeLayer ${value}`)
    }
    function addNewLayer() {
        console.debug(`addNewLayer`)
    }
    function duplicateSelectedLayer() {
        console.debug(`duplicateSelectedLayer ${currentLayerIndex}`)
    }
    function moveSelectedLayerUp() {
        console.debug(`moveSelectedLayerUp ${currentLayerIndex}`)
    }
    function moveSelectedLayerDown() {
        console.debug(`moveSelectedLayerDown ${currentLayerIndex}`)
    }

    // Constraints
    readonly property var parameterNames: [
        'parameter 1',
        'parameter 2',
        'parameter 3'
    ]
    readonly property var relationOperators: ['=', '<', '>']
    readonly property var arithmicOperators: ['', '*', '/', '+', '-']

    // Mock constraints data - matches the new simplified format
    property var constraintsList: [
        {
            dependentName: "Thickness Layer 1",
            expression: "2.0 * parameter 2 + 1.5"
        },
        {
            dependentName: "Roughness Layer 2",
            expression: "parameter 1 / 3.14"
        },
        {
            dependentName: "SLD Layer 3",
            expression: "5.0"
        }
    ]

    function addConstraint(value1, value2, value3, value4, value5) {
        console.debug(`addConstraint ${value1} ${value2} ${value3} ${value4} ${value5}`)

        // Create constraint object in the new simplified format
        let expression = ""
        if (value5 >= 0 && value5 < parameterNames.length) {
            // Parameter-parameter constraint
            expression = `${value3} ${value4} ${parameterNames[value5]}`
        } else {
            // Numeric constraint
            expression = `= ${value3}`
        }

        const constraint = {
            dependentName: parameterNames[value1] || "Unknown",
            expression: expression
        }

        // Add to constraints list - need to reassign the array to trigger property change
        var newConstraints = constraintsList.slice() // Create a copy
        newConstraints.push(constraint)
        constraintsList = newConstraints
        constraintsChanged()
    }

    function removeConstraintByIndex(index) {
        console.debug(`removeConstraintByIndex ${index}`)
        if (index >= 0 && index < constraintsList.length) {
            var newConstraints = constraintsList.slice() // Create a copy
            newConstraints.splice(index, 1)
            constraintsList = newConstraints
            constraintsChanged()
        }
    }

    function toggleConstraintByIndex(index, enabled) {
        console.debug(`toggleConstraintByIndex ${index} ${enabled}`)
        // In a real implementation, this would enable/disable the constraint
    }

    // Q Range
    property double q_min: 4.
    property double q_max: 5.
    property int q_resolution: 6

    // Setters
    function setQMin(value) {
        console.debug(`setQMin ${value}`)
    }
    function setQMax(value) {
        console.debug(`setQMax ${value}`)
    }
    function setQElements(value) {
        console.debug(`setQElements ${value}`)
    }
}
