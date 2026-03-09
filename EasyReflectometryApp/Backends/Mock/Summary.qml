pragma Singleton

import QtQuick

QtObject {
    signal htmlExportingFinished(bool success, string filePath)

    readonly property bool created: true

    readonly property var exportFormats: ["HTML", "PDF"]

    readonly property string fileName: "summary"
    readonly property string plotFileName: "plots"

    readonly property string filePath: '/Users/andpe/ExampleProject/summary'
    readonly property string plotFilePath: '/Users/andpe/ExampleProject/plots'

    readonly property string fileUrl: 'file:///Users/andpe/ExampleProject/summary'
    readonly property string plotFileUrl: 'file:///Users/andpe/ExampleProject/plots'
    readonly property var plotExportFormats: ["PDF", "PNG", "SVG"]

    readonly property string asHtml: '
<!DOCTYPE html>
<html>
<style>
th, td { padding-right: 18px; }
    th { text-align: left; }
</style>
<body>
    <table>
    <tr></tr>
    <tr>
        <td><h1>Summary</h1></td>
    </tr>
    <tr></tr>
    <tr>
        <td><h3>Project information</h3></td>
    </tr>
    <tr></tr>
    <tr>
        <th>Title</th>
        <th>La0.5Ba0.5CoO3</th>
    </tr>
    <tr>
        <td>Description</td>
        <td>neutrons, powder, constant wavelength</td>
    </tr>
    <tr>
        <td>No. of phases</td>
        <td>1</td>
    </tr>
    <tr>
        <td>No. of experiments</td>
        <td>1</td>
    </tr>
    <tr></tr>
        <tr>
            <td><h3>Crystal data</h3></td>
        </tr>
        <tr></tr>
    <tr>
        <th>Phase datablock</th>
        <th>lbco</th>
    </tr>
    <tr>
        <td>Crystal system, space group</td>
        <td>cubic,&nbsp;&nbsp;<i>P m -3 m</i></td>
    </tr>
    <tr></tr>
        <tr>
            <td><h3>Data collection</h3></td>
        </tr>
        <tr></tr>
    <tr>
        <th>Experiment datablock</th>
        <th>hrpt</th>
    </tr>
    <tr>
        <td>Radiation probe</td>
        <td>neutron</td>
    </tr>
    <tr>
        <td>Measured range: min, max, inc (&deg;)</td>
        <td>10.0,&nbsp;&nbsp;164.85,&nbsp;&nbsp;0.05</td>
    </tr>
    <tr></tr>
    </table>
</body>
</html>
'
    function saveAsHtml(path) {
        console.debug(`Saving HTML summary`)
        htmlExportingFinished(true, path)
    }

    function saveAsPdf(path) {
        console.debug(`Saving PDF summary`)
        htmlExportingFinished(true, path)
    }

    function setFileName(value) {
        console.debug(`setFileName ${value}`)
    }

    function setPlotFileName(value) {
        console.debug(`setPlotFileName ${value}`)
    }

    function savePlot(path, widthCm, heightCm) {
        console.debug(`savePlot ${path} ${widthCm} ${heightCm}`)
        htmlExportingFinished(true, path)
    }

    function showPlot(widthCm, heightCm) {
        console.debug(`showPlot ${widthCm} ${heightCm}`)
    }

}
