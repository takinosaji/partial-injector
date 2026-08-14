from spinq.lists import except_, filter_, where_, without_


def is_even(value: int) -> bool:
    return value % 2 == 0


def test_filter_keeps_matching_elements_in_original_order():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    result = filter_(sequence, is_even)

    # Assert
    assert result == [4, 2, 6]


def test_filter_with_no_match_returns_empty_list():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = filter_(sequence, is_even)

    # Assert
    assert result == []


def test_filter_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = filter_(sequence, is_even)

    # Assert
    assert result == []


def test_where_keeps_matching_elements_in_original_order():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    result = where_(sequence, is_even)

    # Assert
    assert result == [4, 2, 6]


def test_where_returns_same_result_as_filter():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    where_result = where_(sequence, is_even)
    filter_result = filter_(sequence, is_even)

    # Assert
    assert where_result == filter_result


def test_without_removes_matching_elements():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    result = without_(sequence, is_even)

    # Assert
    assert result == [1, 3]


def test_without_is_complement_of_filter():
    # Arrange
    sequence = [4, 1, 2, 3, 6]

    # Act
    kept = filter_(sequence, is_even)
    removed = without_(sequence, is_even)

    # Assert
    assert sorted(kept + removed) == sorted(sequence)


def test_without_with_no_match_returns_all_elements():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = without_(sequence, is_even)

    # Assert
    assert result == [1, 3, 5]


def test_without_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = without_(sequence, is_even)

    # Assert
    assert result == []


def test_except_removes_excluded_values():
    # Arrange
    sequence = [1, 2, 3, 4]

    # Act
    result = except_(sequence, [2, 4])

    # Assert
    assert result == [1, 3]


def test_except_removes_every_duplicate_occurrence():
    # Arrange
    sequence = [1, 2, 2, 3, 2]

    # Act
    result = except_(sequence, [2])

    # Assert
    assert result == [1, 3]


def test_except_preserves_order_of_remaining_elements():
    # Arrange
    sequence = [5, 1, 4, 2]

    # Act
    result = except_(sequence, [4])

    # Assert
    assert result == [5, 1, 2]


def test_except_with_empty_exclusions_returns_equal_list():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = except_(sequence, [])

    # Assert
    assert result == [1, 2, 3]


def test_except_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = except_(sequence, [1, 2])

    # Assert
    assert result == []
