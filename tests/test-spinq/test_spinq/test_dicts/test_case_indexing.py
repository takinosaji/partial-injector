import re

import pytest

from spinq.dicts import get_key_by_index_, get_key_value_by_index_

OUT_OF_RANGE_MESSAGE = "Index out of range."


def test_get_key_by_index_returns_key_at_insertion_position():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act
    result = get_key_by_index_(dictionary, 0)

    # Assert
    assert result == "b"


def test_get_key_by_index_returns_middle_key():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act
    result = get_key_by_index_(dictionary, 1)

    # Assert
    assert result == "a"


def test_get_key_by_index_past_end_raises():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(OUT_OF_RANGE_MESSAGE)):
        get_key_by_index_(dictionary, 5)


def test_get_key_by_index_on_empty_dict_raises():
    # Arrange
    dictionary: dict[str, int] = {}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(OUT_OF_RANGE_MESSAGE)):
        get_key_by_index_(dictionary, 0)


def test_get_key_by_index_negative_raises():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act / Assert
    # islice rejects negative indices itself, so the except StopIteration branch never runs
    # and the message comes from CPython rather than from spinq. Only the type is asserted.
    with pytest.raises(ValueError):
        get_key_by_index_(dictionary, -1)


def test_get_key_value_by_index_returns_pair_at_insertion_position():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act
    result = get_key_value_by_index_(dictionary, 0)

    # Assert
    assert result == ("b", 1)


def test_get_key_value_by_index_returns_middle_pair():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act
    result = get_key_value_by_index_(dictionary, 1)

    # Assert
    assert result == ("a", 2)


def test_get_key_value_by_index_past_end_raises():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(OUT_OF_RANGE_MESSAGE)):
        get_key_value_by_index_(dictionary, 5)


def test_get_key_value_by_index_on_empty_dict_raises():
    # Arrange
    dictionary: dict[str, int] = {}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(OUT_OF_RANGE_MESSAGE)):
        get_key_value_by_index_(dictionary, 0)


def test_get_key_value_by_index_negative_raises():
    # Arrange
    dictionary = {"b": 1, "a": 2, "c": 3}

    # Act / Assert
    # islice rejects negative indices itself, so the except StopIteration branch never runs
    # and the message comes from CPython rather than from spinq. Only the type is asserted.
    with pytest.raises(ValueError):
        get_key_value_by_index_(dictionary, -1)
