import pytest

from spinq.lists import distinct_, union_


def test_distinct_removes_duplicates():
    # Arrange
    sequence = [3, 1, 3, 2, 1]

    # Act
    result = distinct_(sequence)

    # Assert
    assert sorted(result) == [1, 2, 3]


def test_distinct_on_already_distinct_list_returns_same_members():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = distinct_(sequence)

    # Assert
    assert sorted(result) == [1, 2, 3]


def test_distinct_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = distinct_(sequence)

    # Assert
    assert result == []


def test_distinct_with_unhashable_elements_raises_type_error():
    # Arrange
    sequence = [[1], [2]]

    # Act / Assert
    # Message comes from CPython's set(), not from spinq, so only the type is asserted.
    with pytest.raises(TypeError):
        distinct_(sequence)


def test_union_returns_distinct_union_of_overlapping_lists():
    # Arrange
    sequence1 = [1, 2, 3]
    sequence2 = [3, 4]

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert set(result) == {1, 2, 3, 4}
    assert len(result) == 4


def test_union_of_disjoint_lists_contains_all_members():
    # Arrange
    sequence1 = [1, 2]
    sequence2 = [3, 4]

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert set(result) == {1, 2, 3, 4}


def test_union_deduplicates_within_a_single_operand():
    # Arrange
    sequence1 = [1, 1, 2]
    sequence2: list[int] = []

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert set(result) == {1, 2}
    assert len(result) == 2


def test_union_with_empty_operand_returns_members_of_other():
    # Arrange
    sequence1: list[int] = []
    sequence2 = [5, 6]

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert set(result) == {5, 6}


def test_union_of_two_empty_lists_returns_empty_list():
    # Arrange
    sequence1: list[int] = []
    sequence2: list[int] = []

    # Act
    result = union_(sequence1, sequence2)

    # Assert
    assert result == []


def test_union_with_unhashable_elements_raises_type_error():
    # Arrange
    sequence1 = [[1]]
    sequence2 = [[2]]

    # Act / Assert
    # Message comes from CPython's set(), not from spinq, so only the type is asserted.
    with pytest.raises(TypeError):
        union_(sequence1, sequence2)
