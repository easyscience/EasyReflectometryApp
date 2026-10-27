from types import SimpleNamespace

from EasyReflectometryApp.Backends.Py.logic.helpers import get_original_name


def test_get_original_name_uses_user_data_value():
    obj = SimpleNamespace(name='Current Name', user_data={'original_name': 'Original Name'})

    assert get_original_name(obj) == 'Original Name'


def test_get_original_name_falls_back_to_name_without_dict_user_data():
    obj = SimpleNamespace(name='Current Name', user_data=None)

    assert get_original_name(obj) == 'Current Name'
