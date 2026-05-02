pragma Singleton

import QtQuick

QtObject {
    property bool available: true

    property var channels: [
        {
            'key': 'pp',
            'label': 'R++',
            'description': 'up-up',
            'color': '#ef4444',
            'enabled': true,
            'hasMeasured': true,
            'hasCalculated': true
        },
        {
            'key': 'mm',
            'label': 'R--',
            'description': 'down-down',
            'color': '#64748b',
            'enabled': true,
            'hasMeasured': true,
            'hasCalculated': true
        },
        {
            'key': 'pm',
            'label': 'R+-',
            'description': 'up-down',
            'color': '#22c55e',
            'enabled': true,
            'hasMeasured': true,
            'hasCalculated': true
        },
        {
            'key': 'mp',
            'label': 'R-+',
            'description': 'down-up',
            'color': '#f97316',
            'enabled': false,
            'hasMeasured': false,
            'hasCalculated': true
        }
    ]

    property var visibleChannelKeys: ['pp', 'mm']
    property bool staggerEnabled: false
    property real staggerFactor: 0.5

    property var sldComponents: [
        {
            'key': 'nuclear',
            'label': 'Nuclear',
            'symbol': 'rho_n',
            'color': '#f59e0b',
            'enabled': true,
            'available': true
        },
        {
            'key': 'magnetic',
            'label': 'Magnetic',
            'symbol': 'rho_m',
            'color': '#14b8a6',
            'enabled': true,
            'available': true
        }
    ]

    property var visibleSldComponentKeys: ['nuclear', 'magnetic']

    signal displayChanged()
    signal dataChanged()

    function setChannelVisible(channelKey, visible) {
        var keys = visibleChannelKeys.slice()
        var index = keys.indexOf(channelKey)

        if (visible && index === -1) {
            keys.push(channelKey)
        } else if (!visible && index !== -1) {
            keys.splice(index, 1)
        }

        visibleChannelKeys = keys
        displayChanged()
    }

    function setVisibleChannelKeys(channelKeys) {
        visibleChannelKeys = channelKeys.slice()
        displayChanged()
    }

    function setStaggerEnabled(value) {
        staggerEnabled = value
        displayChanged()
    }

    function setStaggerFactor(value) {
        staggerFactor = value
        displayChanged()
    }

    function setSldComponentVisible(componentKey, visible) {
        var keys = visibleSldComponentKeys.slice()
        var index = keys.indexOf(componentKey)

        if (visible && index === -1) {
            keys.push(componentKey)
        } else if (!visible && index !== -1) {
            keys.splice(index, 1)
        }

        visibleSldComponentKeys = keys
        displayChanged()
    }

    function setVisibleSldComponentKeys(componentKeys) {
        visibleSldComponentKeys = componentKeys.slice()
        displayChanged()
    }

    function getExperimentChannels(experimentIndex) {
        return channels
    }

    function getAnalysisChannelDataPoints(experimentIndex, channelKey) {
        var channelOffsets = {
            'pp': 0.0,
            'mm': -0.45,
            'pm': -0.9,
            'mp': -1.35
        }
        var offset = channelOffsets[channelKey] || 0.0
        var experimentOffset = experimentIndex * 0.12
        var points = []

        for (var i = 0; i < 80; i++) {
            var q = 0.01 + i * 0.0035
            var decay = -1.5 - q * 9.0
            var oscillation = Math.sin(q * 70.0 + experimentIndex * 0.4) * 0.18
            var calculated = decay + oscillation + offset - experimentOffset
            points.push({
                'x': q,
                'measured': calculated + Math.cos(q * 95.0) * 0.08,
                'calculated': calculated
            })
        }

        return points
    }

    function getSampleChannelDataPoints(modelIndex, channelKey) {
        var channelOffsets = {
            'pp': 0.0,
            'mm': -0.35,
            'pm': -0.75,
            'mp': -1.1
        }
        var offset = channelOffsets[channelKey] || 0.0
        var modelOffset = modelIndex * 0.18
        var points = []

        for (var i = 0; i < 80; i++) {
            var q = 0.01 + i * 0.0035
            var decay = -1.35 - q * 8.2
            var oscillation = Math.sin(q * 62.0 + modelIndex * 0.55) * 0.16
            points.push({
                'x': q,
                'y': decay + oscillation + offset - modelOffset
            })
        }

        return points
    }

    function getSldComponentDataPoints(modelIndex, componentKey) {
        var points = []
        var modelOffset = modelIndex * 0.35

        for (var i = 0; i < 80; i++) {
            var z = i * 3.0
            var layerWave = Math.sin(z / 22.0 + modelIndex * 0.5)
            var interfaceWave = Math.cos(z / 11.0) * 0.15
            var y = componentKey === 'magnetic'
                    ? 0.9 * Math.sin(z / 28.0 + 0.8) + modelOffset * 0.25
                    : 2.2 + layerWave * 0.45 + interfaceWave + modelOffset
            points.push({ 'x': z, 'y': y })
        }

        return points
    }

    function getSpinAsymmetryDataPoints(experimentIndex) {
        var x = []
        var measured = []
        var sigma = []
        var calculated = []

        for (var i = 0; i < 80; i++) {
            var q = 0.01 + i * 0.0035
            var value = 0.28 * Math.sin(q * 45.0 + experimentIndex * 0.3) * Math.exp(-q * 1.2)
            x.push(q)
            calculated.push(value)
            measured.push(value + Math.cos(q * 80.0) * 0.025)
            sigma.push(0.035 + q * 0.02)
        }

        return ({
            'x': x,
            'measured': measured,
            'sigma': sigma,
            'calculated': calculated
        })
    }

    function getPolarizationResidualDataPoints(experimentIndex, channelKey) {
        var phaseByChannel = {
            'pp': 0.0,
            'mm': 0.7,
            'pm': 1.4,
            'mp': 2.1
        }
        var phase = phaseByChannel[channelKey] || 0.0
        var points = []

        for (var i = 0; i < 80; i++) {
            var q = 0.01 + i * 0.0035
            points.push({
                'x': q,
                'y': Math.sin(q * 90.0 + phase + experimentIndex * 0.4) * 0.07
            })
        }

        return points
    }
}
