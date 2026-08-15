import re

import pytest

from spinq.dicts import first_, first_or_none_

NO_MATCH_MESSAGE = "No elements match the predicate."


def is_even(value: int) -> bool:
    return value % 2 == 0


def test_first_applies_predicate_to_values_not_keys():
    # Arrange
    dictionary = {2: 3, 3: 4}

    # Act
    result = first_(dictionary, is_even)

    # Assert
    assert result == (3, 4)


def test_first_returns_key_value_tuple():
    # Arrange
    dictionary = {"a": 1, "b": 2}

    # Act
    result = first_(dictionary, is_even)

    # Assert
    assert result == ("b", 2)


def test_first_without_predicate_returns_first_inserted_pair():
    # Arrange
    dictionary = {"b": 1, "a": 2}

    # Act
    result = first_(dictionary)

    # Assert
    assert result == ("b", 1)


def test_first_with_no_match_raises():
    # Arrange
    dictionary = {"a": 1, "b": 3}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        first_(dictionary, is_even)


def test_first_on_empty_dict_raises():
    # Arrange
    dictionary: dict[str, int] = {}

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        first_(dictionary)


def test_first_or_none_applies_predicate_to_values_not_keys():
    # Arrange
    dictionary = {2: 3, 3: 4}

    # Act
    result = first_or_none_(dictionary, is_even)

    # Assert
    assert result == (3, 4)


def test_first_or_none_without_predicate_returns_first_inserted_pair():
    # Arrange
    dictionary = {"b": 1, "a": 2}

    # Act
    result = first_or_none_(dictionary)

    # Assert
    assert result == ("b", 1)


def test_first_or_none_with_no_match_returns_none():
    # Arrange
    dictionary = {"a": 1, "b": 3}

    # Act
    result = first_or_none_(dictionary, is_even)

    # Assert
    assert result is None


def test_first_or_none_on_empty_dict_returns_none():
    # Arrange
    dictionary: dict[str, int] = {}

    # Act
    result = first_or_none_(dictionary)

    # Assert
    assert result is None
