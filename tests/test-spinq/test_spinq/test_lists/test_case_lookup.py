import re

import pytest

from spinq.lists import (
    first_,
    first_or_none_,
    first_or_none_with_index_,
    last_,
    last_or_none_,
    single_,
    single_or_none_,
)

NO_MATCH_MESSAGE = "No elements match the predicate."
MULTIPLE_MATCH_MESSAGE = "More than one element matches the predicate."


def is_even(value: int) -> bool:
    return value % 2 == 0


def test_first_returns_first_matching_element():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = first_(sequence, is_even)

    # Assert
    assert result == 2


def test_first_without_predicate_returns_head():
    # Arrange
    sequence = [7, 8, 9]

    # Act
    result = first_(sequence)

    # Assert
    assert result == 7


def test_first_with_no_match_raises():
    # Arrange
    sequence = [1, 3, 5]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        first_(sequence, is_even)


def test_first_on_empty_list_raises():
    # Arrange
    sequence: list[int] = []

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        first_(sequence)


def test_first_or_none_returns_first_matching_element():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = first_or_none_(sequence, is_even)

    # Assert
    assert result == 2


def test_first_or_none_without_predicate_returns_head():
    # Arrange
    sequence = [7, 8, 9]

    # Act
    result = first_or_none_(sequence)

    # Assert
    assert result == 7


def test_first_or_none_with_no_match_returns_none():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = first_or_none_(sequence, is_even)

    # Assert
    assert result is None


def test_first_or_none_on_empty_list_returns_none():
    # Arrange
    sequence: list[int] = []

    # Act
    result = first_or_none_(sequence)

    # Assert
    assert result is None


def test_first_or_none_with_index_returns_position_in_original_list():
    # Arrange
    sequence = [1, 3, 4, 6]

    # Act
    result = first_or_none_with_index_(sequence, is_even)

    # Assert
    assert result == (2, 4)


def test_first_or_none_with_index_without_predicate_returns_head_at_zero():
    # Arrange
    sequence = [7, 8]

    # Act
    result = first_or_none_with_index_(sequence)

    # Assert
    assert result == (0, 7)


def test_first_or_none_with_index_with_no_match_returns_none():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = first_or_none_with_index_(sequence, is_even)

    # Assert
    assert result is None


def test_first_or_none_with_index_on_empty_list_returns_none():
    # Arrange
    sequence: list[int] = []

    # Act
    result = first_or_none_with_index_(sequence)

    # Assert
    assert result is None


def test_last_returns_last_matching_element():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = last_(sequence, is_even)

    # Assert
    assert result == 4


def test_last_without_predicate_returns_tail():
    # Arrange
    sequence = [7, 8, 9]

    # Act
    result = last_(sequence)

    # Assert
    assert result == 9


def test_last_with_no_match_raises():
    # Arrange
    sequence = [1, 3, 5]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        last_(sequence, is_even)


def test_last_on_empty_list_raises():
    # Arrange
    sequence: list[int] = []

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        last_(sequence)


def test_last_or_none_returns_last_matching_element():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = last_or_none_(sequence, is_even)

    # Assert
    assert result == 4


def test_last_or_none_without_predicate_returns_tail():
    # Arrange
    sequence = [7, 8, 9]

    # Act
    result = last_or_none_(sequence)

    # Assert
    assert result == 9


def test_last_or_none_with_no_match_returns_none():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = last_or_none_(sequence, is_even)

    # Assert
    assert result is None


def test_last_or_none_on_empty_list_returns_none():
    # Arrange
    sequence: list[int] = []

    # Act
    result = last_or_none_(sequence)

    # Assert
    assert result is None


def test_single_returns_sole_matching_element():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = single_(sequence, is_even)

    # Assert
    assert result == 2


def test_single_with_no_match_raises():
    # Arrange
    sequence = [1, 3, 5]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        single_(sequence, is_even)


def test_single_on_empty_list_raises():
    # Arrange
    sequence: list[int] = []

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(NO_MATCH_MESSAGE)):
        single_(sequence, is_even)


def test_single_with_multiple_matches_raises():
    # Arrange
    sequence = [2, 3, 4]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(MULTIPLE_MATCH_MESSAGE)):
        single_(sequence, is_even)


def test_single_or_none_returns_sole_matching_element():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = single_or_none_(sequence, is_even)

    # Assert
    assert result == 2


def test_single_or_none_with_no_match_returns_none():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = single_or_none_(sequence, is_even)

    # Assert
    assert result is None


def test_single_or_none_on_empty_list_returns_none():
    # Arrange
    sequence: list[int] = []

    # Act
    result = single_or_none_(sequence, is_even)

    # Assert
    assert result is None


def test_single_or_none_with_multiple_matches_raises():
    # Arrange
    sequence = [2, 3, 4]

    # Act / Assert
    with pytest.raises(ValueError, match=re.escape(MULTIPLE_MATCH_MESSAGE)):
        single_or_none_(sequence, is_even)
