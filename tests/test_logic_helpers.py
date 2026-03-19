from types import SimpleNamespace

from EasyReflectometryApp.Backends.Py.logic.helpers import IO
from EasyReflectometryApp.Backends.Py.logic.helpers import get_original_name


def test_format_msg_main_prefix_and_columns():
    message = IO.formatMsg('main', 'alpha', 'beta')

    assert message.startswith('* ')
    assert 'alpha' in message
    assert 'beta' in message
    assert ' ▌ ' in message


def test_format_msg_sub_prefix():
    message = IO.formatMsg('sub', 'alpha')

    assert message.startswith('  - ')


def test_get_original_name_uses_user_data_value():
    obj = SimpleNamespace(name='Current Name', user_data={'original_name': 'Original Name'})

    assert get_original_name(obj) == 'Original Name'


def test_get_original_name_falls_back_to_name_without_dict_user_data():
    obj = SimpleNamespace(name='Current Name', user_data=None)

    assert get_original_name(obj) == 'Current Name'