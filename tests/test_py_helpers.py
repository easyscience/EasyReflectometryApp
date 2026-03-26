import warnings

from EasyReflectometryApp.Backends.Py import helpers as helpers_module


def test_generalize_path_non_windows_returns_parsed_path(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'linux')

    result = helpers_module.IO.generalizePath('file:///tmp/demo/file.dat')

    assert result == '/tmp/demo/file.dat'


def test_generalize_path_windows_strips_leading_slash_and_normalizes(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'win32')

    result = helpers_module.IO.generalizePath('/C:/demo/folder/file.dat')

    assert result == 'C:\\demo\\folder\\file.dat'


def test_local_file_to_url_windows_branch(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'win32')

    result = helpers_module.IO.localFileToUrl('C:/demo/folder/file.dat')

    assert result.startswith('file:///')
    assert '/demo/folder/file.dat' in result


def test_to_std_dev_smallest_precision_for_large_std_dev():
    value_str, std_dev_str, combined = helpers_module.IO.toStdDevSmalestPrecision(12.7, 2.6)

    assert value_str == '13'
    assert std_dev_str == '3'
    assert combined == '13(3)'


def test_to_std_dev_smallest_precision_for_fractional_std_dev():
    value_str, std_dev_str, combined = helpers_module.IO.toStdDevSmalestPrecision(12.345, 0.034)

    assert value_str == '12.35'
    assert std_dev_str == '0.03'
    assert combined == '12.35(3)'


def test_old_precision_formatter_still_returns_three_parts():
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        value_str, std_dev_str, combined = helpers_module.IO.toStdDevSmalestPrecision_OLD(1.23, 0.04)

    assert value_str
    assert std_dev_str
    assert '(' in combined and ')' in combined
