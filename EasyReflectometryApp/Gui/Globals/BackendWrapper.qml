pragma Singleton

import QtQuick

import Backends as Backends

// Wrapper to external backend API to expose properties and methods to the QML GUI.
// Backend implementations are located in the Backends folder.
// Serves to decouple the GUI code from the backend code.
// - In GUI code, backend properties and methods MUST be accessed through this object.
// - The backend is instantiated at runtime based on the availability of the PyBackend class.
// - A flat structure is used.
// -- Enable QT Creator to show the properties in the editor (code completion and rightclick follow).
// -- Location of property in backend should be encoded in the name.
// -- Should implement setters for properties that are writable, onChanged breaks the link to the property.

QtObject {

    ///////////////
    // Active backend
    ///////////////
    // Instantiate MockBackend if PyBackend is not defined otherwise use PyBackend
    // The PyBackend class will be defined if exposed from main.py
    readonly property var activeBackend: {
        if (typeof Backends.PyBackend == 'undefined') {
            console.debug('MOCK backend is in use')
            return Backends.MockBackend
        } else {
            console.debug('PYTHON backend proxy is in use')
            return Backends.PyBackend
        }
    }
    readonly property bool testMode: {
        if (typeof isTestMode == 'undefined') {
            return false
        } else{ 
            return isTestMode
        }
    }

    /////////////
    // Status bar
    /////////////
    readonly property string statusProject: activeBackend.status.project
    readonly property string statusPhaseCount: activeBackend.status.phaseCount
    readonly property string statusExperimentsCount: activeBackend.status.experimentsCount
    readonly property string statusCalculator: activeBackend.status.calculator
    readonly property string statusMinimizer: activeBackend.status.minimizer
    readonly property string statusVariables: activeBackend.status.variables


    ///////////////
    // Home page
    ///////////////
    readonly property string homeVersionNumber: activeBackend.home.version.number
    readonly property string homeVersionDate: activeBackend.home.version.date
    readonly property string homeUrlsHomepage: activeBackend.home.urls.homepage
    readonly property string homeUrlsIssues: activeBackend.home.urls.issues
    readonly property string homeUrlsLicense: activeBackend.home.urls.license
    readonly property string homeUrlsDocumentation: activeBackend.home.urls.documentation
    readonly property string homeUrlsDependencies: activeBackend.home.urls.dependencies


    ///////////////
    // Project page
    ///////////////
    readonly property bool projectCreated: activeBackend.project.created
    readonly property string projectCreationDate: activeBackend.project.creationDate

    readonly property string projectName: activeBackend.project.name
    function projectSetName(value) { activeBackend.project.setName(value) } 
    readonly property string projectDescription: activeBackend.project.description
    function projectSetDescription(value) { activeBackend.project.setDescription(value) } 
    readonly property string projectLocation: activeBackend.project.location
    function projectSetLocation(value) { activeBackend.project.setLocation(value) } 

    function projectCreate() { activeBackend.project.create() }
    function projectReset() { activeBackend.project.reset() }
    function projectSave() { activeBackend.project.save() }
    function projectLoad(value) { activeBackend.project.load(value) }
    function sampleFileLoad(value) { activeBackend.project.sampleLoad(value) }


    ///////////////
    // Sample page
    ///////////////

    // Material
    readonly property var sampleMaterials: activeBackend.sample.materials
    readonly property var sampleMaterialNames: activeBackend.sample.materialNames

    readonly property int sampleCurrentMaterialIndex: activeBackend.sample.currentMaterialIndex
    function sampleSetCurrentMaterialIndex(value) { activeBackend.sample.setCurrentMaterialIndex(value) }

    function sampleSetCurrentMaterialName(value) { activeBackend.sample.setCurrentMaterialName(value) }
    function sampleSetCurrentMaterialSld(value) { activeBackend.sample.setCurrentMaterialSld(value) } 
    function sampleSetCurrentMaterialISld(value) { activeBackend.sample.setCurrentMaterialISld(value) }
    function sampleRemoveMaterial(value) { activeBackend.sample.removeMaterial(value) }
    function sampleAddNewMaterial() { activeBackend.sample.addNewMaterial() }
    function sampleDuplicateSelectedMaterial() { activeBackend.sample.duplicateSelectedMaterial() }
    function sampleMoveSelectedMaterialUp() { activeBackend.sample.moveSelectedMaterialUp() }
    function sampleMoveSelectedMaterialDown() { activeBackend.sample.moveSelectedMaterialDown() }

    // Model
    readonly property var sampleModels: activeBackend.sample.models
    readonly property var sampleModelNames: activeBackend.sample.modelsNames
    readonly property string sampleCurrentModelName: activeBackend.sample.currentModelName

    readonly property int sampleCurrentModelIndex: activeBackend.sample.currentModelIndex
    function sampleSetCurrentModelIndex(value) { activeBackend.sample.setCurrentModelIndex(value) }

    function sampleSetCurrentModelName(value) { activeBackend.sample.setCurrentModelName(value) }
    function sampleRemoveModel(value) { activeBackend.sample.removeModel(value) }
    function sampleAddNewModel() { activeBackend.sample.addNewModel() }
    function sampleDuplicateSelectedModel() { activeBackend.sample.duplicateSelectedModel() }
    function sampleMoveSelectedModelUp() { activeBackend.sample.moveSelectedModelUp() }
    function sampleMoveSelectedModelDown() { activeBackend.sample.moveSelectedModelDown() }

    // Sample
    readonly property var sampleAssemblies: activeBackend.sample.assemblies
    readonly property string sampleCurrentAssemblyName: activeBackend.sample.currentAssemblyName
    readonly property string sampleCurrentAssemblyType: activeBackend.sample.currentAssemblyType

    readonly property int sampleCurrentAssemblyIndex: activeBackend.sample.currentAssemblyIndex
    function sampleSetCurrentAssemblyIndex(value) { activeBackend.sample.setCurrentAssemblyIndex(value) }

    function sampleSetCurrentAssemblyName(value) { activeBackend.sample.setCurrentAssemblyName(value) }
    function sampleSetCurrentAssemblyType(value) { activeBackend.sample.setCurrentAssemblyType(value) }
    function sampleRemoveAssembly(value) { activeBackend.sample.removeAssembly(value) }
    function sampleAddNewAssembly() { activeBackend.sample.addNewAssembly() }
    function sampleDuplicateSelectedAssembly() { activeBackend.sample.duplicateSelectedAssembly() }
    function sampleMoveSelectedAssemblyUp() { activeBackend.sample.moveSelectedAssemblyUp() }
    function sampleMoveSelectedAssemblyDown() { activeBackend.sample.moveSelectedAssemblyDown() }

    // Assembly specific methods
    readonly property int sampleCurrentAssemblyRepeatedLayerReptitions: activeBackend.sample.currentAssemblyRepeatedLayerReptitions
    function sampleSetCurrentAssemblyConstrainAPM(value) { activeBackend.sample.setCurrentAssemblyConstrainAPM(value) }
    function sampleSetCurrentAssemblyConformalRoughness(value) { activeBackend.sample.setCurrentAssemblyConformalRoughness(value) }
    function sampleSetCurrentAssemblyRepeatedLayerReptitions(value) { activeBackend.sample.setCurrentAssemblyRepeatedLayerReptitions(value) }

    // Layer
    readonly property var sampleLayers: activeBackend.sample.layers
    readonly property string sampleCurrentLayerName: activeBackend.sample.currentLayerName

    readonly property int sampleCurrentLayerIndex: activeBackend.sample.currentLayerIndex
    function sampleSetCurrentLayerIndex(value) { activeBackend.sample.setCurrentLayerIndex(value) }

    function sampleRemoveLayer(value) { activeBackend.sample.removeLayer(value) }
    function sampleAddNewLayer() { activeBackend.sample.addNewLayer() }
    function sampleDuplicateSelectedLayer() { activeBackend.sample.duplicateSelectedLayer() }
    function sampleMoveSelectedLayerUp() { activeBackend.sample.moveSelectedLayerUp() }
    function sampleMoveSelectedLayerDown() { activeBackend.sample.moveSelectedLayerDown() }

    function sampleSetCurrentLayerFormula(value) { activeBackend.sample.setCurrentLayerFormula(value) }
    function sampleSetCurrentLayerMaterial(value) { activeBackend.sample.setCurrentLayerMaterial(value) }
    function sampleSetCurrentLayerSolvent(value) { activeBackend.sample.setCurrentLayerSolvent(value) }
    function sampleSetCurrentLayerThickness(value) { activeBackend.sample.setCurrentLayerThickness(value) }
    function sampleSetCurrentLayerRoughness(value) { activeBackend.sample.setCurrentLayerRoughness(value) }
    function sampleSetCurrentLayerAPM(value) { activeBackend.sample.setCurrentLayerAPM(value) }
    function sampleSetCurrentLayerSolvation(value) { activeBackend.sample.setCurrentLayerSolvation(value) }

    // Constraints
    readonly property var sampleEnabledParameterNames: activeBackend.sample.enabledParameterNames
    readonly property var sampleParameterNames: activeBackend.sample.parameterNames
    readonly property var sampleDepParameterNames: activeBackend.sample.dependentParameterNames
    readonly property var sampleRelationOperators: activeBackend.sample.relationOperators
    readonly property var sampleArithmicOperators: activeBackend.sample.arithmicOperators
    readonly property var sampleConstraintsList: activeBackend.sample.constraintsList
    readonly property var sampleConstraintParametersMetadata: activeBackend.sample.constraintParametersMetadata

    function sampleValidateConstraintExpression(index, relation, expression) { return activeBackend.sample.validateConstraintExpression(index, relation, expression) }
    function sampleAddConstraint(index, relation, expression) { return activeBackend.sample.addConstraint(index, relation, expression) }
    function sampleRemoveConstraintByIndex(value) { activeBackend.sample.removeConstraintByIndex(value) }
    function sampleConstrainModelsParameters(modelIndices) { activeBackend.sample.constrainModelsParameters(modelIndices) }

    // Q range
    readonly property var sampleQMin: activeBackend.sample.q_min
    function sampleSetQMin(value) { activeBackend.sample.setQMin(value) }
    readonly property var sampleQMax: activeBackend.sample.q_max
    function sampleSetQMax(value) { activeBackend.sample.setQMax(value) }
    readonly property var sampleQResolution: activeBackend.sample.q_resolution
    function sampleSetQElements(value) { activeBackend.sample.setQElements(value) }

    //////////////////
    // Experiment page
    //////////////////
    readonly property bool experimentExperimentalData: activeBackend.experiment.experimentalData

    readonly property var experimentScaling: activeBackend.experiment.scaling
    function experimentSetScaling(value) { activeBackend.experiment.setScaling(value) }
    readonly property var experimentBackground: activeBackend.experiment.background
    function experimentSetBackground(value) { activeBackend.experiment.setBackground(value) }
    readonly property var experimentResolution: activeBackend.experiment.resolution
    function experimentSetResolution(value) { activeBackend.experiment.setResolution(value) }
    function experimentLoad(value) { activeBackend.experiment.load(value) }


    ///////////////
    // Analysis page
    ///////////////
    readonly property var analysisExperimentsAvailable: activeBackend.analysis.experimentsAvailable
    readonly property int analysisExperimentsCurrentIndex: activeBackend.analysis.experimentCurrentIndex
    function analysisSetExperimentsCurrentIndex(value) { activeBackend.analysis.setExperimentCurrentIndex(value) }
    function analysisRemoveExperiment(value) { activeBackend.analysis.removeExperiment(value) }
    
    // Multi-experiment selection support
    readonly property int analysisExperimentsSelectedCount: {
        try {
            return activeBackend.analysisExperimentsSelectedCount || 1
        } catch (e) {
            return 1
        }
    }
    readonly property var analysisSelectedExperimentIndices: {
        try {
            return activeBackend.analysisSelectedExperimentIndices || []
        } catch (e) {
            return []
        }
    }
    function analysisSetSelectedExperimentIndices(value) {
        try {
            activeBackend.analysisSetSelectedExperimentIndices(value)
        } catch (e) {
            console.warn("Failed to set selected experiment indices:", e)
        }
    }

    function analysisSetModelOnExperiment(value) { activeBackend.analysis.setModelOnExperiment(value) }
    readonly property var analysisModelForExperiment: activeBackend.analysis.modelIndexForExperiment
    readonly property var modelNamesForExperiment: activeBackend.analysis.modelNamesForExperiment
    readonly property var modelColorsForExperiment: activeBackend.analysis.modelColorsForExperiment
    
    readonly property var analysisCalculatorsAvailable: activeBackend.analysis.calculatorsAvailable
    readonly property int analysisCalculatorCurrentIndex: activeBackend.analysis.calculatorCurrentIndex
    function analysisSetCalculatorCurrentIndex(value) { activeBackend.analysis.setCalculatorCurrentIndex(value) }

    readonly property var analysisMinimizersAvailable: activeBackend.analysis.minimizersAvailable
    readonly property int analysisMinimizerCurrentIndex: activeBackend.analysis.minimizerCurrentIndex
    function analysisSetMinimizerCurrentIndex(value) { activeBackend.analysis.setMinimizerCurrentIndex(value) }

    readonly property var analysisFitableParameters: activeBackend.analysis.enabledParameters
    readonly property int analysisCurrentParameterIndex: activeBackend.analysis.currentParameterIndex
    readonly property var analysisEnabledParameters: activeBackend.analysis.enabledParameters

    function analysisSetCurrentParameterIndex(value) { activeBackend.analysis.setCurrentParameterIndex(value) }
    function analysisSetExperimentName(value) { activeBackend.analysis.setExperimentName(value) }
    function analysisSetExperimentNameAtIndex(index, value) { activeBackend.analysis.setExperimentNameAtIndex(index, value) }

    // Minimizer
    readonly property var analysisMinimizerTolerance: activeBackend.analysis.minimizerTolerance
    function analysisSetMinimizerTolerance(value) { activeBackend.analysis.setMinimizerTolerance(value) }
    readonly property var analysisMinimizerMaxIterations: activeBackend.analysis.minimizerMaxIterations
    function analysisSetMinimizerMaxIterations(value) { activeBackend.analysis.setMinimizerMaxIterations(value) }

    // Fitting
    readonly property string analysisFittingStatus: activeBackend.analysis.fittingStatus
    readonly property bool analysisFittingRunning: activeBackend.analysis.fittingRunning
    readonly property bool analysisIsFitFinished: activeBackend.analysis.isFitFinished
    readonly property bool analysisShowFitResultsDialog: activeBackend.analysis.showFitResultsDialog
    readonly property bool analysisFitSuccess: activeBackend.analysis.fitSuccess
    readonly property string analysisFitErrorMessage: activeBackend.analysis.fitErrorMessage
    readonly property int analysisFitNumRefinedParams: activeBackend.analysis.fitNumRefinedParams
    readonly property real analysisFitChi2: activeBackend.analysis.fitChi2
    readonly property var analysisFitResults: activeBackend.analysis.fitResults
    function analysisFittingStartStop() { activeBackend.analysis.fittingStartStop() }
    function analysisSetShowFitResultsDialog(value) { activeBackend.analysis.setShowFitResultsDialog(value) }
    function analysisStopFit() { activeBackend.analysis.stopFit() }

    // Fit failure signal - forwarded from backend
    signal analysisFitFailed(string message)

    // Connect backend fitFailed signal to QML signal
    property var _fitFailedConnection: {
        if (activeBackend && activeBackend.analysis && activeBackend.analysis.fitFailed) {
            activeBackend.analysis.fitFailed.connect(analysisFitFailed)
        }
        return null
    }

    // Parameters
    readonly property int analysisFreeParametersCount: activeBackend.analysis.freeParametersCount
    readonly property int analysisFixedParametersCount: activeBackend.analysis.fixedParametersCount
    readonly property int analysisModelParametersCount: activeBackend.analysis.modelParametersCount
    readonly property int analysisExperimentParametersCount: activeBackend.analysis.experimentParametersCount

    function analysisSetCurrentParameterValue(value) { activeBackend.analysis.setCurrentParameterValue(value) }
    function analysisSetCurrentParameterMin(value) { activeBackend.analysis.setCurrentParameterMin(value) }
    function analysisSetCurrentParameterMax(value) { activeBackend.analysis.setCurrentParameterMax(value) }
    function analysisSetCurrentParameterFit(value) { activeBackend.analysis.setCurrentParameterFit(value) }

    ///////////////
    // Summary page
    ///////////////
    readonly property bool summaryCreated: activeBackend.summary.created
    readonly property string summaryAsHtml: activeBackend.summary.asHtml
    readonly property string summaryFileName: activeBackend.summary.fileName
    readonly property string summaryFilePath: activeBackend.summary.filePath
    readonly property string summaryFileUrl: activeBackend.summary.fileUrl
    readonly property var summaryExportFormats: activeBackend.summary.exportFormats

    function summarySetFileName(value) { activeBackend.summary.setFileName(value) }
    function summarySaveAsHtml() { activeBackend.summary.saveAsHtml() }
    function summarySaveAsPdf() { activeBackend.summary.saveAsPdf() }


    ///////////////
    // Plotting
    ///////////////
    readonly property var plottingSldMinX: activeBackend.plotting.sldMinX
    readonly property var plottingSldMaxX: activeBackend.plotting.sldMaxX
    readonly property var plottingSldMinY: activeBackend.plotting.sldMinY
    readonly property var plottingSldMaxY: activeBackend.plotting.sldMaxY

    readonly property var plottingSampleMinX: activeBackend.plotting.sampleMinX
    readonly property var plottingSampleMaxX: activeBackend.plotting.sampleMaxX
    readonly property var plottingSampleMinY: activeBackend.plotting.sampleMinY
    readonly property var plottingSampleMaxY: activeBackend.plotting.sampleMaxY

    readonly property var plottingExperimentMinX: activeBackend.plotting.experimentMinX
    readonly property var plottingExperimentMaxX: activeBackend.plotting.experimentMaxX
    readonly property var plottingExperimentMinY: activeBackend.plotting.experimentMinY
    readonly property var plottingExperimentMaxY: activeBackend.plotting.experimentMaxY

    readonly property var plottingAnalysisMinX: activeBackend.plotting.sampleMinX
    readonly property var plottingAnalysisMaxX: activeBackend.plotting.sampleMaxX
    readonly property var plottingAnalysisMinY: activeBackend.plotting.sampleMinY
    readonly property var plottingAnalysisMaxY: activeBackend.plotting.sampleMaxY
    readonly property var calcSerieColor: activeBackend.plotting.calcSerieColor

    // Plot mode properties
    readonly property bool plottingPlotRQ4: activeBackend.plotting.plotRQ4
    readonly property string plottingYAxisTitle: activeBackend.plotting.yMainAxisTitle
    readonly property bool plottingXAxisLog: activeBackend.plotting.xAxisLog
    readonly property string plottingXAxisType: activeBackend.plotting.xAxisType
    readonly property bool plottingSldXReversed: activeBackend.plotting.sldXDataReversed

    // Reference line visibility
    readonly property bool plottingScaleShown: activeBackend.plotting.scaleShown
    readonly property bool plottingBkgShown: activeBackend.plotting.bkgShown

    // Plot mode toggle functions
    function plottingTogglePlotRQ4() { activeBackend.plotting.togglePlotRQ4() }
    function plottingToggleXAxisType() { activeBackend.plotting.toggleXAxisType() }
    function plottingReverseSldXData() { activeBackend.plotting.reverseSldXData() }
    function plottingFlipScaleShown() { activeBackend.plotting.flipScaleShown() }
    function plottingFlipBkgShown() { activeBackend.plotting.flipBkgShown() }

    // Reference line data accessors
    function plottingGetBackgroundData() {
        try {
            return activeBackend.plotting.getBackgroundData()
        } catch (e) {
            return []
        }
    }
    function plottingGetScaleData() {
        try {
            return activeBackend.plotting.getScaleData()
        } catch (e) {
            return []
        }
    }

    // Analysis-specific reference line data accessors (use sample/calculated x-range)
    function plottingGetBackgroundDataForAnalysis() {
        try {
            return activeBackend.plotting.getBackgroundDataForAnalysis()
        } catch (e) {
            return []
        }
    }
    function plottingGetScaleDataForAnalysis() {
        try {
            return activeBackend.plotting.getScaleDataForAnalysis()
        } catch (e) {
            return []
        }
    }

    function plottingSetQtChartsSerieRef(value1, value2, value3) { activeBackend.plotting.setQtChartsSerieRef(value1, value2, value3) }
    function plottingRefreshSample() { activeBackend.plotting.drawCalculatedOnSampleChart() }
    function plottingRefreshSLD() { activeBackend.plotting.drawCalculatedOnSldChart() }
    function plottingRefreshExperiment() { activeBackend.plotting.drawMeasuredOnExperimentChart() }
    function plottingRefreshAnalysis() { activeBackend.plotting.drawCalculatedAndMeasuredOnAnalysisChart() }

    // Multi-model sample page plotting support
    readonly property int plottingModelCount: activeBackend.plotting.modelCount
    function plottingGetSampleDataPointsForModel(index) {
        try {
            return activeBackend.plotting.getSampleDataPointsForModel(index)
        } catch (e) {
            return []
        }
    }
    function plottingGetSldDataPointsForModel(index) {
        try {
            return activeBackend.plotting.getSldDataPointsForModel(index)
        } catch (e) {
            return []
        }
    }
    function plottingGetModelColor(index) {
        try {
            return activeBackend.plotting.getModelColor(index)
        } catch (e) {
            return '#000000'
        }
    }

    // Signal for sample page data changes - forward from backend
    signal samplePageDataChanged()
    // Signal for plot mode changes - forward from backend
    signal plotModeChanged()

    // Connect to backend signal (called from Component.onCompleted in QML items)
    function connectSamplePageDataChanged() {
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.samplePageDataChanged) {
            activeBackend.plotting.samplePageDataChanged.connect(samplePageDataChanged)
        }
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.plotModeChanged) {
            activeBackend.plotting.plotModeChanged.connect(plotModeChanged)
        }
    }

    Component.onCompleted: {
        connectSamplePageDataChanged()
    }

    // Multi-experiment plotting support
    readonly property bool plottingIsMultiExperimentMode: {
        try {
            return activeBackend.plottingIsMultiExperimentMode || false
        } catch (e) {
            return false
        }
    }
    readonly property var plottingIndividualExperimentDataList: {
        try {
            return activeBackend.plottingIndividualExperimentDataList || []
        } catch (e) {
            return []
        }
    }
    function plottingGetExperimentDataPoints(index) {
        try {
            return activeBackend.plottingGetExperimentDataPoints(index)
        } catch (e) {
            return []
        }
    }
    function plottingGetAnalysisDataPoints(index) {
        try {
            return activeBackend.plottingGetAnalysisDataPoints(index)
        } catch (e) {
            return []
        }
    }
}
