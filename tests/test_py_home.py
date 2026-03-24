from EasyReflectometryApp.Backends.Py.home import Home


def test_home_version_contains_number_and_date(qcore_application):
    home = Home()

    version = home.version

    assert set(version.keys()) == {'number', 'date'}
    assert isinstance(version['number'], str)
    assert isinstance(version['date'], str)
    assert version['number']


def test_home_urls_contains_expected_keys(qcore_application):
    home = Home()

    urls = home.urls

    assert set(urls.keys()) == {'homepage', 'issues', 'license', 'documentation', 'dependencies'}
    for value in urls.values():
        assert isinstance(value, str)
        assert value
