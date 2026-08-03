import os
import sys
from urllib.parse import urlparse

import numpy as np
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication
from uncertainties import ufloat


class IO:
    @staticmethod
    def generalizePath(fpath: str) -> str:
        """
        Generalize the filepath to be platform-specific, so all file operations
        can be performed.
        :param URI rcfPath: URI to the file
        :return URI filename: platform specific URI
        """
        filename = urlparse(fpath).path
        if not sys.platform.startswith('win'):
            return filename
        if filename[0] == '/':
            filename = filename[1:].replace('/', os.path.sep)
        return filename

    @staticmethod
    def localFileToUrl(fpath: str) -> str:
        return QUrl.fromLocalFile(fpath).toString()

    @staticmethod
    def formatMsg(type, *args):
        types = {'main': '*', 'sub': '  -'}
        mark = types[type]
        widths = [22, 21, 20, 10]
        widths[0] -= len(mark)
        msgs = []
        for idx, arg in enumerate(args):
            msgs.append(f'{arg:<{widths[idx]}}')
        msg = ' ▌ '.join(msgs)
        msg = f'{mark} {msg}'
        return msg

    @staticmethod
    def toStdDevSmalestPrecision(value, std_dev):
        if std_dev > 1:
            value_str = f'{round(value)}'
            std_dev_str = f'{round(std_dev)}'
            value_with_std_dev_str = f'{value_str}({std_dev_str})'
        else:
            precision = 1
            std_dev_decimals = precision - int(np.floor(np.log10(std_dev) + 1))
            std_dev = round(std_dev, std_dev_decimals)
            std_dev_str = f'{std_dev:.{std_dev_decimals}f}'
            value = round(value, std_dev_decimals)
            value_str = f'{value:.{std_dev_decimals}f}'
            clipped_std_dev = int(round(std_dev * 10**std_dev_decimals))
            value_with_std_dev_str = f'{value_str}({clipped_std_dev})'
        return value_str, std_dev_str, value_with_std_dev_str

    @staticmethod
    def toStdDevSmalestPrecision_OLD(value, std_dev):
        if std_dev < 10:
            fmt = '.1u'
        else:
            fmt = 'u'
        value_str, std_dev_str = f'{ufloat(value, std_dev):{fmt}}'.split('+/-')
        value_with_std_dev_str = f'{ufloat(value, std_dev):{fmt}S}'
        return value_str, std_dev_str, value_with_std_dev_str

    # def value_with_error_WEB(val, err, precision=2):
    #     """String with value and error in parenthesis with the number of digits given by precision."""
    #     # Number of digits in the error
    #     err_decimals = precision - int(np.floor(np.log10(err) + 1))
    #     # Output error with a "precision" number of significant digits
    #     err_out = round(err, err_decimals)
    #     # Removes leading zeros for fractional errors
    #     if err_out < 1:
    #         err_out = int(round(err_out * 10**err_decimals))
    #         err_format = 0
    #     else:
    #         err_format = int(np.clip(err_decimals, 0, np.inf))

    #     # Format the value to have the same significant digits as the error
    #     val_out = round(val, err_decimals)
    #     val_format = int(np.clip(err_decimals, 0, np.inf))

    #     return f'{val_out:.{val_format}f}({err_out:.{err_format}f})'


class Application(QApplication):  # QGuiApplication crashes when using in combination with QtCharts
    def __init__(self, sysArgv):
        super(Application, self).__init__(sysArgv)
        self.setApplicationName('EasyReflectometry')
        self.setOrganizationName('EasyScience')
        self.setOrganizationDomain('easyscience.software')
