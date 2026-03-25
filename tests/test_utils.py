import pytest

from dify_client import models, utils


def test_str_to_enum_returns_member():
    result = utils.str_to_enum(models.StreamEvent, "message")
    assert result == models.StreamEvent.MESSAGE


def test_str_to_enum_returns_default_when_ignored():
    sentinel = object()
    result = utils.str_to_enum(models.StreamEvent, "not-exist", ignore_not_found=True, enum_default=sentinel)
    assert result is sentinel


def test_str_to_enum_raises_when_not_found():
    with pytest.raises(ValueError):
        utils.str_to_enum(models.StreamEvent, "not-exist")
