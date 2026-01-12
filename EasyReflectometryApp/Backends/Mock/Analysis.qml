pragma Singleton

import QtQuick

QtObject {
    readonly property var minimizersAvailable: ['minimizer_1', 'minimizer_2', 'minimizer_3']
    readonly property int minimizerCurrentIndex: 0

    readonly property var calculatorsAvailable: ['calculator_1', 'calculator_2', 'calculator_3']
    readonly property int calculatorCurrentIndex: 1

    readonly property var experimentsAvailable: ['experiment_1', 'experiment_2', 'experiment_3']
    readonly property int experimentCurrentIndex: 2

    // Minimizer
    readonly property double minimizerTolerance: 1.0
    readonly property int minimizerMaxIterations: 2

    // Fitting
    readonly property string fittingStatus: ''//undefined  //'Success'
    readonly property bool isFitFinished: true
    readonly property bool fittingRunning: false
    property bool showFitResultsDialog: false
    readonly property bool fitSuccess: true
    readonly property int fitNumRefinedParams: 3
    readonly property real fitChi2: 1.2345

    // Parameters
    property int currentParameterIndex: 0
    readonly property int modelParametersCount: 10
    readonly property int experimentParametersCount: 20
    readonly property int freeParametersCount: 100
    readonly property int fixedParametersCount: 200
    readonly property var fitableParameters: [
        {
            'name': 'name 1',
            'value': 1.0,
            'error': -1.23456,
            'max': 100.0,
            'min': -100.0,
            'units': 'u1',
            'fit': true,
            'from': -10.0,
            'to': 10.0,
        },
        {
            'name': 'name 2',
            'value': 2.0,
            'error': -2.34567,
            'max': 200.0,
            'min': -200.0,
            'units': 'u2',
            'fit': false,
            'from': -20.0,
            'to': 20.0,
        },
        {
            'name': 'name 3',
            'value': 3.0,
            'error': -3.45678,
            'max': 300.0,
            'min': -300.0,
            'units': 'u3',
            'fit': true,
            'from': -30.0,
            'to': 30.0,
        },
    ]
    function setCurrentParameterMin(value) {
        console.debug(`setCurrentParameterMin ${value}`)
    }
    function setCurrentParameterMax(value) {
        console.debug(`setCurrentParameterMax ${value}`)
    }
    function setCurrentParameterValue(value) {
        console.debug(`setCurrentParameterValue ${value}`)
    }
    function setCurrentParameterFit(value) {
        console.debug(`setCurrentParameterFit ${value}`)
    }

    // Setters
    function setCurrentParameterIndex(value) {
        currentParameterIndex = value
        console.debug(`setCurrentParameterIndex ${value}`)
    }
    function setCalculatorCurrentIndex(value) {
        console.debug(`setCalculatorCurrentIndex ${value}`)
    }
    function setExperimentCurrentIndex(value) {
        console.debug(`setExperimentCurrentIndex ${value}`)
    }
    function setMinimizerCurrentIndex(value) {
        console.debug(`setMinimizer ${value}`)
    }
    function setMinimizerTolerance(value) {
        console.debug(`setMinimizerTolerance ${value}`)
    }
    function setMinimizerMaxIterations(value) {
        console.debug(`setMinimizerMaxIterations ${value}`)
    }

    //Actions
    function fittingStartStop() {
        console.debug('fittingStartStop')
    }
    function setShowFitResultsDialog(value) {
        showFitResultsDialog = value
        console.debug(`setShowFitResultsDialog ${value}`)
    }
}
