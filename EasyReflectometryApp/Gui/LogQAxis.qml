import QtQuick
import QtCharts

// Logarithmic q axis that keeps its ticks and labels when zoomed in.
//
// LogValueAxis places ticks (and so labels and grid lines) only at integer
// powers of `base`. With base 10, a zoom window inside one decade (say
// 0.02-0.08 Å⁻¹) contains no tick at all and the axis goes blank. So the base
// follows the visible range: 10 while at least two decade ticks are in view,
// otherwise 10^(1/k), with k picked to put about `minTicks` ticks in the
// window. Changing the base moves only the ticks: the log mapping of data to
// pixels, log(q/min) / log(max/min), does not depend on it.
//
// Minor ticks (unlabelled grid lines) fill the gaps between labelled ticks:
// at 2×, 3×, ... 9× of each decade with base 10, and `zoomMinorTicks` evenly
// spaced ones between the ticks of a fractional base.
//
// The axis line itself is hidden: the chart's PlotFrame draws the border.
LogValueAxis {
    id: axis

    property int minTicks: 4
    property int zoomMinorTicks: 4

    base: 10
    labelFormat: '%.3g'
    // -1: Qt picks floor(base) - 2 minor ticks per decade, i.e. 2…9 for base 10.
    minorTickCount: -1
    lineVisible: false

    onMinChanged: updateTicks()
    onMaxChanged: updateTicks()

    function updateTicks() {
        // Zooming sets min and max one after the other, so a transiently
        // inverted or non-positive range is possible here; skip it.
        if (!(min > 0) || !(max > min))
            return
        const decades = Math.log10(max / min)
        // While two decade ticks are in view (as in the usual unzoomed q
        // range), plain decades read best and the axis looks as it always did.
        const decadeTicks = Math.floor(Math.log10(max)) - Math.ceil(Math.log10(min)) + 1
        if (decadeTicks >= 2) {
            base = 10
            labelFormat = '%.3g'
            minorTickCount = -1
            return
        }
        // Ticks fall every 1/k decade, so a window of `decades` holds at
        // least floor(decades * k) of them.
        const k = Math.ceil(minTicks / decades)
        base = Math.pow(10, 1 / k)
        // Qt's automatic count, floor(base) - 2, is zero for a base below 3.
        minorTickCount = zoomMinorTicks
        // Enough significant digits for neighbouring ticks (a factor `base`
        // apart) to print differently.
        const digits = Math.max(3, Math.ceil(-Math.log10(base - 1)) + 1)
        labelFormat = '%.' + digits + 'g'
    }
}
