pragma Singleton

import QtQuick

QtObject {

    readonly property var about: {
        'name': 'EasyReflectometry',
        'namePrefixForLogo': 'easy',
        'nameSuffixForLogo': 'reflectometry',
        'icon': Qt.resolvedUrl('../Resources/Logo/App.svg'),
        'developerYearsFrom': '2019',
        'developerYearsTo': '2025',
        'description': 'EasyReflectometry is a scientific software for \nmodelling and analysis of \nneutron and x-ray reflecometry data. \n\nEasyReflectometry is build by ESS DMSC in \nCopenhagen, Denmark.',
        'developerIcons': [
            {
                'url': 'https://ess.eu',
                'icon': Qt.resolvedUrl('../Resources/Logo/ESS.png'),
                'heightScale': 3.0
            }
        ]
    }

}

