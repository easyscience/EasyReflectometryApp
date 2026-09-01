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
    readonly property string statusModelsCount: activeBackend.status.modelsCount
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
    function sampleFileLoad(value, append) { activeBackend.project.sampleLoad(value, append) }

    // Sample load warning signal - forwarded from backend
    signal sampleLoadWarning(string message)

    property var _sampleLoadWarningConnection: {
        if (activeBackend && activeBackend.project && activeBackend.project.sampleLoadWarning) {
            activeBackend.project.sampleLoadWarning.connect(sampleLoadWarning)
        }
        return null
    }

    // Project load error signal - forwarded from backend
    signal projectLoadError(string message)

    property var _projectLoadErrorConnection: {
        if (activeBackend && activeBackend.project && activeBackend.project.projectLoadError) {
            activeBackend.project.projectLoadError.connect(projectLoadError)
        }
        return null
    }


    ///////////////
    // Sample page
    ///////////////

    // Material
    readonly property var sampleMaterials: activeBackend.sample.materials
    readonly property var sampleMaterialNames: activeBackend.sample.materialNames

    readonly property int sampleCurrentMaterialIndex: activeBackend.sample.currentMaterialIndex
    function sampleSetCurrentMaterialIndex(value) { activeBackend.sample.setCurrentMaterialIndex(value) }

    function sampleSetCurrentMaterialName(value) { activeBackend.sample.setCurrentMaterialName(value) }
    function sampleSetMaterialNameAtIndex(index, value) { activeBackend.sample.setMaterialNameAtIndex(index, value) }
    function sampleSetCurrentMaterialSld(value) { activeBackend.sample.setCurrentMaterialSld(value) }
    function sampleSetMaterialSldAtIndex(index, value) { activeBackend.sample.setMaterialSldAtIndex(index, value) }
    function sampleSetCurrentMaterialISld(value) { activeBackend.sample.setCurrentMaterialISld(value) }
    function sampleSetMaterialISldAtIndex(index, value) { activeBackend.sample.setMaterialISldAtIndex(index, value) }
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
    function sampleSetModelNameAtIndex(index, value) { activeBackend.sample.setModelNameAtIndex(index, value) }
    function sampleRemoveModel(value) { activeBackend.sample.removeModel(value) }
    function sampleAddNewModel() { activeBackend.sample.addNewModel() }
    function sampleDuplicateSelectedModel() { activeBackend.sample.duplicateSelectedModel() }
    function sampleMoveSelectedModelUp() { activeBackend.sample.moveSelectedModelUp() }
    function sampleMoveSelectedModelDown() { activeBackend.sample.moveSelectedModelDown() }

    // Calculation engine (project-wide; also exposed on the Analysis page)
    readonly property var sampleCalculationEngines: {
        try {
            return activeBackend.sample.calculationEngines || []
        } catch (e) {
            return []
        }
    }
    readonly property int sampleCalculationEngineIndex: {
        try {
            return activeBackend.sample.calculationEngineIndex || 0
        } catch (e) {
            return 0
        }
    }
    readonly property var sampleCalculationEnginesSupportingMagnetism: {
        try {
            return activeBackend.sample.calculationEnginesSupportingMagnetism || []
        } catch (e) {
            return []
        }
    }
    function sampleSetCalculationEngineIndex(value) {
        try {
            activeBackend.sample.setCalculationEngineIndex(value)
        } catch (e) {
            console.warn("sampleSetCalculationEngineIndex failed:", e)
        }
    }
    function sampleEnableMagnetismWithEngineAtIndex(index, engine) {
        try {
            activeBackend.sample.enableMagnetismWithEngineAtIndex(index, engine)
        } catch (e) {
            console.warn("sampleEnableMagnetismWithEngineAtIndex failed:", e)
        }
    }

    // Sample
    readonly property var sampleAssemblies: activeBackend.sample.assemblies
    readonly property string sampleCurrentAssemblyName: activeBackend.sample.currentAssemblyName
    readonly property string sampleCurrentAssemblyType: activeBackend.sample.currentAssemblyType

    readonly property int sampleCurrentAssemblyIndex: activeBackend.sample.currentAssemblyIndex
    function sampleSetCurrentAssemblyIndex(value) { activeBackend.sample.setCurrentAssemblyIndex(value) }

    function sampleSetCurrentAssemblyName(value) { activeBackend.sample.setCurrentAssemblyName(value) }
    function sampleSetAssemblyNameAtIndex(index, value) { activeBackend.sample.setAssemblyNameAtIndex(index, value) }
    function sampleSetCurrentAssemblyType(value) { activeBackend.sample.setCurrentAssemblyType(value) }
    function sampleSetAssemblyTypeAtIndex(index, value) { activeBackend.sample.setAssemblyTypeAtIndex(index, value) }
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

    // Structure view (flattened whole-stack representation)
    readonly property var sampleStructure: activeBackend.sample.structure
    readonly property var sampleStructureLegend: activeBackend.sample.structureLegend
    readonly property real sampleStructureTotalThickness: activeBackend.sample.structureTotalThickness

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
    function sampleSetLayerFormulaAtIndex(index, value) { activeBackend.sample.setLayerFormulaAtIndex(index, value) }
    function sampleSetCurrentLayerMaterial(value) { activeBackend.sample.setCurrentLayerMaterial(value) }
    function sampleSetLayerMaterialAtIndex(index, value) { activeBackend.sample.setLayerMaterialAtIndex(index, value) }
    function sampleSetCurrentLayerSolvent(value) { activeBackend.sample.setCurrentLayerSolvent(value) }
    function sampleSetLayerSolventAtIndex(index, value) { activeBackend.sample.setLayerSolventAtIndex(index, value) }
    function sampleSetCurrentLayerThickness(value) { activeBackend.sample.setCurrentLayerThickness(value) }
    function sampleSetLayerThicknessAtIndex(index, value) { activeBackend.sample.setLayerThicknessAtIndex(index, value) }
    function sampleSetCurrentLayerRoughness(value) { activeBackend.sample.setCurrentLayerRoughness(value) }
    function sampleSetLayerRoughnessAtIndex(index, value) { activeBackend.sample.setLayerRoughnessAtIndex(index, value) }
    function sampleSetCurrentLayerAPM(value) { activeBackend.sample.setCurrentLayerAPM(value) }
    function sampleSetLayerAPMAtIndex(index, value) { activeBackend.sample.setLayerAPMAtIndex(index, value) }
    function sampleSetCurrentLayerSolvation(value) { activeBackend.sample.setCurrentLayerSolvation(value) }
    function sampleSetLayerSolvationAtIndex(index, value) { activeBackend.sample.setLayerSolvationAtIndex(index, value) }

    // Layer magnetism (polarized analysis). Only the refl1d calculator can
    // model magnetic layers, so the editor is gated on sampleMagnetismSupported.
    readonly property bool sampleMagnetismSupported: {
        try {
            return activeBackend.sample.magnetismSupported || false
        } catch (e) {
            return false
        }
    }
    readonly property var sampleLayersMagnetism: {
        try {
            return activeBackend.sample.layersMagnetism || []
        } catch (e) {
            console.warn("sampleLayersMagnetism failed:", e)
            return []
        }
    }
    function sampleSetLayerMagneticAtIndex(index, value) { activeBackend.sample.setLayerMagneticAtIndex(index, value) }
    function sampleSetLayerRhoMAtIndex(index, value) { activeBackend.sample.setLayerRhoMAtIndex(index, value) }
    function sampleSetLayerThetaMAtIndex(index, value) { activeBackend.sample.setLayerThetaMAtIndex(index, value) }

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

    // Inequality constraints (BUMPS-only fit penalties) and physics-constraint recipes
    readonly property int sampleInequalityConstraintsCount: activeBackend.sample.inequalityConstraintsCount
    readonly property var sampleViolatedInequalityConstraints: activeBackend.sample.violatedInequalityConstraints
    readonly property var samplePhysicsConstraintRecipes: activeBackend.sample.physicsConstraintRecipes
    // Note: the backends also expose setInequalityConstraintEnabled(index, enabled)
    // (disable-without-delete); wrap it here once the constraints table grows a
    // per-row enable control.
    function sampleApplyPhysicsConstraint(assemblyIndex, recipeId) { return activeBackend.sample.applyPhysicsConstraint(assemblyIndex, recipeId) }
    function sampleRemovePhysicsConstraint(assemblyIndex, recipeId) { return activeBackend.sample.removePhysicsConstraint(assemblyIndex, recipeId) }

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
    // Polarized experiment import (one file per spin channel)
    function experimentSuggestPolarizedChannels(value) { return activeBackend.experiment.suggestPolarizedChannels(value) }
    // Returns '' on success, or the reason the import was rejected. The backend
    // validates the rows itself and raises, which would otherwise surface only
    // as an uncaught slot exception.
    function experimentLoadPolarized(value) {
        try {
            activeBackend.experiment.loadPolarized(value)
        } catch (e) {
            console.warn("experimentLoadPolarized failed:", e)
            return (e && e.message) ? e.message : qsTr("The polarized experiment could not be loaded.")
        }
        return ''
    }


    ///////////////
    // Analysis page
    ///////////////
    readonly property var analysisExperimentsAvailable: activeBackend.analysis.experimentsAvailable
    readonly property var analysisExperimentsPolarized: {
        try {
            return activeBackend.analysis.experimentsPolarized || []
        } catch (e) {
            return []
        }
    }
    // Measured spin channels per experiment (0 when unpolarized), shown next to
    // the polarization badge in the experiment lists.
    readonly property var analysisExperimentsChannelCount: {
        try {
            return activeBackend.analysis.experimentsChannelCount || []
        } catch (e) {
            return []
        }
    }
    readonly property int analysisExperimentsCurrentIndex: activeBackend.analysis.experimentCurrentIndex
    function analysisSetExperimentsCurrentIndex(value) { activeBackend.analysis.setExperimentCurrentIndex(value) }
    function analysisRemoveExperiment(value) { activeBackend.analysis.removeExperiment(value) }
    
    // Multi-experiment selection support
    readonly property int analysisExperimentsSelectedCount: {
        try {
            return activeBackend.analysisExperimentsSelectedCount || 1
        } catch (e) {
            console.warn("analysisExperimentsSelectedCount failed:", e)
            return 1
        }
    }
    readonly property var analysisSelectedExperimentIndices: {
        try {
            return activeBackend.analysisSelectedExperimentIndices || []
        } catch (e) {
            console.warn("analysisSelectedExperimentIndices failed:", e)
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
    readonly property int analysisFitIteration: activeBackend.analysis.fitIteration
    readonly property real analysisFitInterimChi2: activeBackend.analysis.fitInterimChi2
    readonly property real analysisFitInterimReducedChi2: activeBackend.analysis.fitInterimReducedChi2
    readonly property string analysisFitProgressMessage: activeBackend.analysis.fitProgressMessage
    readonly property bool analysisFitHasInterimUpdate: activeBackend.analysis.fitHasInterimUpdate
    readonly property bool analysisFitHasPreviewUpdate: activeBackend.analysis.fitHasPreviewUpdate
    readonly property var analysisFitPreviewParameterValues: activeBackend.analysis.fitPreviewParameterValues
    readonly property var analysisFitResults: activeBackend.analysis.fitResults
    function analysisFittingStartStop() { activeBackend.analysis.fittingStartStop() }
    function analysisSetShowFitResultsDialog(value) { activeBackend.analysis.setShowFitResultsDialog(value) }
    function analysisStopFit() { activeBackend.analysis.stopFit() }

    // Bayesian sampling
    readonly property bool analysisIsBayesianSelected: activeBackend.analysis.isBayesianSelected
    readonly property bool analysisMinimizerSupportsInequalities: activeBackend.analysis.minimizerSupportsInequalities
    readonly property string analysisInequalityConstraintsWarning: activeBackend.analysis.inequalityConstraintsWarning
    readonly property bool analysisFitInfeasible: activeBackend.analysis.fitInfeasible

    readonly property int bayesianSamples: activeBackend.analysis.bayesianSamples
    readonly property int bayesianBurnIn: activeBackend.analysis.bayesianBurnIn
    readonly property int bayesianPopulation: activeBackend.analysis.bayesianPopulation
    readonly property int bayesianThinning: activeBackend.analysis.bayesianThinning

    function bayesianSetSamples(v)    { activeBackend.analysis.setBayesianSamples(v) }
    function bayesianSetBurnIn(v)     { activeBackend.analysis.setBayesianBurnIn(v) }
    function bayesianSetPopulation(v) { activeBackend.analysis.setBayesianPopulation(v) }
    function bayesianSetThinning(v)   { activeBackend.analysis.setBayesianThinning(v) }

    readonly property string bayesianInitializer: activeBackend.analysis.bayesianInitializer
    readonly property var bayesianInitializerOptions: activeBackend.analysis.bayesianInitializerOptions
    function setBayesianInitializer(v) { activeBackend.analysis.setBayesianInitializer(v) }

    readonly property var bayesianPosterior: activeBackend.analysis.bayesianPosterior
    readonly property bool bayesianResultAvailable: activeBackend.analysis.bayesianResultAvailable
    readonly property var bayesianMarginals: activeBackend.analysis.bayesianMarginals

    // Phase 2: corner/trace/distribution plots (HTML), diagnostics, heatmap
    readonly property string bayesianCornerPlotUrl: activeBackend.analysis.bayesianCornerPlotUrl
    readonly property string bayesianTracePlotUrl: activeBackend.analysis.bayesianTracePlotUrl
    readonly property string bayesianDistributionPlotUrl: activeBackend.analysis.bayesianDistributionPlotUrl
    readonly property var bayesianDiagnostics: activeBackend.analysis.bayesianDiagnostics
    readonly property var bayesianParamNames: activeBackend.analysis.bayesianParamNames
    readonly property var bayesianHeatmapData: activeBackend.analysis.bayesianHeatmapData
    readonly property string bayesianHeatmapPlotUrl: activeBackend.analysis.bayesianHeatmapPlotUrl
    function bayesianComputeHeatmap(x, y) { activeBackend.analysis.computeBayesianHeatmap(x, y) }
    function bayesianSavePlot(sourceUrl)  { activeBackend.analysis.saveBayesianPlot(sourceUrl) }

    // Phase 2: SLD posterior predictive
    readonly property var posteriorPredictiveSldZ: activeBackend.plotting.posteriorPredictiveSldZ
    readonly property var posteriorPredictiveSldMedian: activeBackend.plotting.posteriorPredictiveSldMedian
    readonly property var posteriorPredictiveSldLower: activeBackend.plotting.posteriorPredictiveSldLower
    readonly property var posteriorPredictiveSldUpper: activeBackend.plotting.posteriorPredictiveSldUpper

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
    readonly property string analysisNameFilterCriteria: activeBackend.analysis.nameFilterCriteria
    readonly property string analysisVariabilityFilterCriteria: activeBackend.analysis.variabilityFilterCriteria

    function analysisSetCurrentParameterValue(value) { activeBackend.analysis.setCurrentParameterValue(value) }
    function analysisSetCurrentParameterMin(value) { activeBackend.analysis.setCurrentParameterMin(value) }
    function analysisSetCurrentParameterMax(value) { activeBackend.analysis.setCurrentParameterMax(value) }
    function analysisSetCurrentParameterFit(value) { activeBackend.analysis.setCurrentParameterFit(value) }
    function analysisSetNameFilterCriteria(value) { activeBackend.analysis.setNameFilterCriteria(value) }
    function analysisSetVariabilityFilterCriteria(value) { activeBackend.analysis.setVariabilityFilterCriteria(value) }

    ///////////////
    // Summary page
    ///////////////
    readonly property bool summaryCreated: activeBackend.summary.created
    readonly property string summaryAsHtml: activeBackend.summary.asHtml
    readonly property string summaryFileName: activeBackend.summary.fileName
    readonly property string summaryFilePath: activeBackend.summary.filePath
    readonly property string summaryFileUrl: activeBackend.summary.fileUrl
    readonly property var summaryExportFormats: activeBackend.summary.exportFormats
    readonly property string summaryPlotFileName: activeBackend.summary.plotFileName
    readonly property string summaryPlotFilePath: activeBackend.summary.plotFilePath
    readonly property string summaryPlotFileUrl: activeBackend.summary.plotFileUrl
    readonly property var summaryPlotExportFormats: activeBackend.summary.plotExportFormats

    function summarySetFileName(value) { activeBackend.summary.setFileName(value) }
    function summarySetPlotFileName(value) { activeBackend.summary.setPlotFileName(value) }
    function summarySaveAsHtml(path) { activeBackend.summary.saveAsHtml(path) }
    function summarySaveAsPdf(path) { activeBackend.summary.saveAsPdf(path) }
    function summarySavePlot(path, widthCm, heightCm) { activeBackend.summary.savePlot(path, widthCm, heightCm) }
    function summaryShowPlot(widthCm, heightCm) { activeBackend.summary.showPlot(widthCm, heightCm) }

    signal summaryExportingFinished(bool success, string filePath)

    property var _summaryExportConnection: {
        if (activeBackend && activeBackend.summary && activeBackend.summary.htmlExportingFinished) {
            activeBackend.summary.htmlExportingFinished.connect(summaryExportingFinished)
        }
        return null
    }


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

    readonly property var plottingResidualMinX: activeBackend.plotting.residualMinX
    readonly property var plottingResidualMaxX: activeBackend.plotting.residualMaxX
    readonly property var plottingResidualMinY: activeBackend.plotting.residualMinY
    readonly property var plottingResidualMaxY: activeBackend.plotting.residualMaxY

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

    // Posterior predictive (Bayesian) overlay data
    readonly property var posteriorPredictiveQ: activeBackend.plotting.posteriorPredictiveQ
    readonly property var posteriorPredictiveMedian: activeBackend.plotting.posteriorPredictiveMedian
    readonly property var posteriorPredictiveLower: activeBackend.plotting.posteriorPredictiveLower
    readonly property var posteriorPredictiveUpper: activeBackend.plotting.posteriorPredictiveUpper

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
            console.warn("plottingGetBackgroundData failed:", e)
            return []
        }
    }
    function plottingGetScaleData() {
        try {
            return activeBackend.plotting.getScaleData()
        } catch (e) {
            console.warn("plottingGetScaleData failed:", e)
            return []
        }
    }

    // Analysis-specific reference line data accessors (use sample/calculated x-range)
    function plottingGetBackgroundDataForAnalysis() {
        try {
            return activeBackend.plotting.getBackgroundDataForAnalysis()
        } catch (e) {
            console.warn("plottingGetBackgroundDataForAnalysis failed:", e)
            return []
        }
    }
    function plottingGetScaleDataForAnalysis() {
        try {
            return activeBackend.plotting.getScaleDataForAnalysis()
        } catch (e) {
            console.warn("plottingGetScaleDataForAnalysis failed:", e)
            return []
        }
    }

    // Helper to update background/scale reference line series on any chart view.
    // useAnalysisRange: true for Analysis charts (sample x-range), false for Experiment charts.
    function updateRefLines(bkgSeries, scaleSeries, useAnalysisRange) {
        bkgSeries.clear()
        if (plottingBkgShown) {
            var bkgData = useAnalysisRange ? plottingGetBackgroundDataForAnalysis() : plottingGetBackgroundData()
            for (var i = 0; i < bkgData.length; i++) {
                bkgSeries.append(bkgData[i].x, bkgData[i].y)
            }
        }
        scaleSeries.clear()
        if (plottingScaleShown) {
            var scaleData = useAnalysisRange ? plottingGetScaleDataForAnalysis() : plottingGetScaleData()
            for (var j = 0; j < scaleData.length; j++) {
                scaleSeries.append(scaleData[j].x, scaleData[j].y)
            }
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
            console.warn("plottingGetSampleDataPointsForModel failed:", e)
            return []
        }
    }
    function plottingGetSldDataPointsForModel(index) {
        try {
            return activeBackend.plotting.getSldDataPointsForModel(index)
        } catch (e) {
            console.warn("plottingGetSldDataPointsForModel failed:", e)
            return []
        }
    }
    // One-call series fills (false = backend cannot fill, caller falls back
    // to an append() loop — e.g. the mock backend).
    function plottingFillSampleSeriesForModel(series, index) {
        try {
            activeBackend.plotting.fillSampleSeriesForModel(series, index)
            return true
        } catch (e) {
            return false
        }
    }
    function plottingFillSldSeriesForModel(series, index) {
        try {
            activeBackend.plotting.fillSldSeriesForModel(series, index)
            return true
        } catch (e) {
            return false
        }
    }
    function plottingFillMagneticSldSegmentSeries(series, index, curve, segment) {
        try {
            activeBackend.plotting.fillMagneticSldSegmentSeries(series, index, curve, segment)
            return true
        } catch (e) {
            return false
        }
    }
    function plottingGetModelColor(index) {
        try {
            return activeBackend.plotting.getModelColor(index)
        } catch (e) {
            console.warn("plottingGetModelColor failed:", e)
            return '#000000'
        }
    }

    // Signal for sample page data changes - forward from backend
    signal samplePageDataChanged()
    // Signal for resetting chart axes after data load
    signal samplePageResetAxes()
    // Signal for plot mode changes - forward from backend
    signal plotModeChanged()
    // Signal to request QML to reset chart axes (e.g., after model load)
    signal chartAxesResetRequested()
    // Signal for posterior predictive (Bayesian) overlay data updates
    signal posteriorPredictiveDataChanged()
    // Signal for posterior predictive SLD (Bayesian) overlay data updates
    signal posteriorPredictiveSldDataChanged()
    // Magnetic display state changed: which magnetic curves are drawn (SLD
    // chart), whether the sample chart splits a model into its spin
    // cross-sections, or whether any model is magnetic at all
    signal magneticProfileChanged()
    // Spin-asymmetry availability or content changed
    signal spinAsymmetryChanged()

    // Connect to backend signal (called from Component.onCompleted in QML items)
    function connectSamplePageDataChanged() {
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.samplePageDataChanged) {
            activeBackend.plotting.samplePageDataChanged.connect(samplePageDataChanged)
        }
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.samplePageResetAxes) {
            activeBackend.plotting.samplePageResetAxes.connect(samplePageResetAxes)
        }
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.plotModeChanged) {
            activeBackend.plotting.plotModeChanged.connect(plotModeChanged)
        }
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.chartAxesResetRequested) {
            activeBackend.plotting.chartAxesResetRequested.connect(chartAxesResetRequested)
        }
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.posteriorPredictiveDataChanged) {
            activeBackend.plotting.posteriorPredictiveDataChanged.connect(posteriorPredictiveDataChanged)
        }
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.posteriorPredictiveSldDataChanged) {
            activeBackend.plotting.posteriorPredictiveSldDataChanged.connect(posteriorPredictiveSldDataChanged)
        }
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.magneticProfileChanged) {
            activeBackend.plotting.magneticProfileChanged.connect(magneticProfileChanged)
        }
        if (activeBackend && activeBackend.plotting && activeBackend.plotting.spinAsymmetryChanged) {
            activeBackend.plotting.spinAsymmetryChanged.connect(spinAsymmetryChanged)
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
            console.warn("plottingIsMultiExperimentMode failed:", e)
            return false
        }
    }
    readonly property var plottingIndividualExperimentDataList: {
        try {
            return activeBackend.plottingIndividualExperimentDataList || []
        } catch (e) {
            console.warn("plottingIndividualExperimentDataList failed:", e)
            return []
        }
    }
    // Same list, but a polarized experiment appears once per visible spin
    // channel — for charts that draw per-channel series.
    readonly property var plottingIndividualExperimentChannelDataList: {
        try {
            return activeBackend.plottingIndividualExperimentChannelDataList || []
        } catch (e) {
            console.warn("plottingIndividualExperimentChannelDataList failed:", e)
            return []
        }
    }
    function plottingGetExperimentDataPoints(index) {
        try {
            return activeBackend.plottingGetExperimentDataPoints(index)
        } catch (e) {
            console.warn("plottingGetExperimentDataPoints failed:", e)
            return []
        }
    }
    // `channel` is optional: pass a spin channel ('pp'/'pm'/'mp'/'mm') to get
    // that cross-section of a polarized experiment, '' for the ordinary curve.
    function plottingGetAnalysisDataPoints(index, channel) {
        try {
            return activeBackend.plottingGetAnalysisDataPoints(index, channel || "")
        } catch (e) {
            console.warn("plottingGetAnalysisDataPoints failed:", e)
            return []
        }
    }
    function plottingGetResidualDataPoints(index, channel) {
        try {
            return activeBackend.plottingGetResidualDataPoints(index, channel || "")
        } catch (e) {
            console.warn("plottingGetResidualDataPoints failed:", e)
            return []
        }
    }
    // True when the analysis/residual charts must draw one series per channel.
    readonly property bool plottingAnalysisUsesChannelSeries: {
        try {
            return activeBackend.plottingAnalysisUsesChannelSeries || false
        } catch (e) {
            return false
        }
    }

    // Polarized experiment (spin channel) plotting support
    readonly property bool plottingCurrentExperimentIsPolarized: {
        try {
            return activeBackend.plotting.currentExperimentIsPolarized || false
        } catch (e) {
            console.warn("plottingCurrentExperimentIsPolarized failed:", e)
            return false
        }
    }
    readonly property var plottingExperimentChannelList: {
        try {
            return activeBackend.plotting.experimentChannelList || []
        } catch (e) {
            console.warn("plottingExperimentChannelList failed:", e)
            return []
        }
    }
    function plottingGetExperimentChannels(index) {
        try {
            return activeBackend.plottingGetExperimentChannels(index)
        } catch (e) {
            console.warn("plottingGetExperimentChannels failed:", e)
            return []
        }
    }
    function plottingGetExperimentChannelDataPoints(index, channel) {
        try {
            return activeBackend.plottingGetExperimentChannelDataPoints(index, channel)
        } catch (e) {
            console.warn("plottingGetExperimentChannelDataPoints failed:", e)
            return []
        }
    }
    function plottingSetChannelVisible(channel, visible) {
        try {
            activeBackend.plottingSetChannelVisible(channel, visible)
        } catch (e) {
            console.warn("plottingSetChannelVisible failed:", e)
        }
    }

    // Magnetic depth profiles on the shared SLD chart (Sample and Analysis)
    readonly property bool plottingAnyModelHasMagnetism: {
        try {
            return activeBackend.plotting.anyModelHasMagnetism || false
        } catch (e) {
            return false
        }
    }
    readonly property var plottingVisibleSldCurves: {
        try {
            return activeBackend.plotting.visibleSldCurves || []
        } catch (e) {
            return []
        }
    }
    readonly property string plottingMagneticProfileError: {
        try {
            return activeBackend.plotting.magneticProfileError || ''
        } catch (e) {
            return ''
        }
    }
    readonly property var plottingSldThetaMinY: {
        try {
            return activeBackend.plotting.sldThetaMinY
        } catch (e) {
            return 0
        }
    }
    readonly property var plottingSldThetaMaxY: {
        try {
            return activeBackend.plotting.sldThetaMaxY
        } catch (e) {
            return 360
        }
    }
    function plottingModelHasMagnetism(index) {
        try {
            return activeBackend.plottingModelHasMagnetism(index)
        } catch (e) {
            return false
        }
    }
    function plottingGetMagneticSldDataPointsForModel(index, curve) {
        try {
            return activeBackend.plottingGetMagneticSldDataPointsForModel(index, curve)
        } catch (e) {
            console.warn("plottingGetMagneticSldDataPointsForModel failed:", e)
            return []
        }
    }
    function plottingGetMagneticSldSegmentsForModel(index, curve) {
        try {
            return activeBackend.plottingGetMagneticSldSegmentsForModel(index, curve)
        } catch (e) {
            console.warn("plottingGetMagneticSldSegmentsForModel failed:", e)
            return []
        }
    }
    function plottingGetMagneticSldSegment(index, curve, segment) {
        try {
            return activeBackend.plottingGetMagneticSldSegment(index, curve, segment)
        } catch (e) {
            console.warn("plottingGetMagneticSldSegment failed:", e)
            return []
        }
    }
    function plottingSldCurveVisible(curve) {
        try {
            return activeBackend.plottingSldCurveVisible(curve)
        } catch (e) {
            return false
        }
    }
    function plottingSetSldCurveVisible(curve, visible) {
        try {
            activeBackend.plottingSetSldCurveVisible(curve, visible)
        } catch (e) {
            console.warn("plottingSetSldCurveVisible failed:", e)
        }
    }

    // Model spin cross-sections on the sample page reflectivity chart
    readonly property bool plottingShowModelChannels: {
        try {
            return activeBackend.plotting.showModelChannels || false
        } catch (e) {
            return false
        }
    }
    function plottingSetShowModelChannels(visible) {
        try {
            activeBackend.plotting.setShowModelChannels(visible)
        } catch (e) {
            console.warn("plottingSetShowModelChannels failed:", e)
        }
    }
    function plottingFillSampleChannelSeriesForModel(series, index, channel) {
        try {
            activeBackend.plotting.fillSampleChannelSeriesForModel(series, index, channel)
        } catch (e) {
            console.warn("plottingFillSampleChannelSeriesForModel failed:", e)
        }
    }

    // Spin asymmetry
    readonly property bool plottingSpinAsymmetryAvailable: {
        try {
            return activeBackend.plotting.spinAsymmetryAvailable || false
        } catch (e) {
            return false
        }
    }
    readonly property bool plottingSpinAsymmetryCalculatedAvailable: {
        try {
            return activeBackend.plotting.spinAsymmetryCalculatedAvailable || false
        } catch (e) {
            return false
        }
    }
    readonly property int plottingSpinAsymmetryMaskedPoints: {
        try {
            return activeBackend.plotting.spinAsymmetryMaskedPoints || 0
        } catch (e) {
            return 0
        }
    }
    readonly property int plottingSpinAsymmetryOutOfOverlapPoints: {
        try {
            return activeBackend.plotting.spinAsymmetryOutOfOverlapPoints || 0
        } catch (e) {
            return 0
        }
    }
    readonly property var plottingSpinAsymmetryMinX: {
        try {
            return activeBackend.plotting.spinAsymmetryMinX
        } catch (e) {
            return 0
        }
    }
    readonly property var plottingSpinAsymmetryMaxX: {
        try {
            return activeBackend.plotting.spinAsymmetryMaxX
        } catch (e) {
            return 1
        }
    }
    readonly property var plottingSpinAsymmetryMinY: {
        try {
            return activeBackend.plotting.spinAsymmetryMinY
        } catch (e) {
            return -1
        }
    }
    readonly property var plottingSpinAsymmetryMaxY: {
        try {
            return activeBackend.plotting.spinAsymmetryMaxY
        } catch (e) {
            return 1
        }
    }
    function plottingGetSpinAsymmetryPoints(index) {
        try {
            return activeBackend.plottingGetSpinAsymmetryPoints(index)
        } catch (e) {
            console.warn("plottingGetSpinAsymmetryPoints failed:", e)
            return []
        }
    }
    function plottingGetSpinAsymmetryCalculatedPoints(index) {
        try {
            return activeBackend.plottingGetSpinAsymmetryCalculatedPoints(index)
        } catch (e) {
            console.warn("plottingGetSpinAsymmetryCalculatedPoints failed:", e)
            return []
        }
    }

    // Bayesian sampling progress
    readonly property int analysisSampleProgressStep: activeBackend.analysis.sampleProgressStep
    readonly property string analysisSampleProgressMessage: activeBackend.analysis.sampleProgressMessage
    readonly property bool analysisSampleProgressHasUpdate: activeBackend.analysis.sampleProgressHasUpdate
    readonly property int analysisSampleProgressTotalSteps: activeBackend.analysis.sampleProgressTotalSteps
}
