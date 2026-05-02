pragma Singleton

import QtQuick

import Backends.Mock as Backend

QtObject {

    property var analysis: Backend.Analysis
    property var experiment: Backend.Experiment
    property var home: Backend.Home
    property var project: Backend.Project
    property var summary: Backend.Summary
    property var sample: Backend.Sample
    property var status: Backend.Status
    property var plotting: Backend.Plotting
    property var polarization: Backend.Polarization
    property var helpers: Backend.Helpers
}


