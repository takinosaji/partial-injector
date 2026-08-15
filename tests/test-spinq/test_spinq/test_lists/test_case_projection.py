from spinq.lists import select_, select_many_, where_with_index_


def is_even(value: int) -> bool:
    return value % 2 == 0


def double(value: int) -> int:
    return value * 2


def test_select_applies_selector_to_every_element():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = select_(sequence, double)

    # Assert
    assert result == [2, 4, 6]


def test_select_preserves_order_and_length():
    # Arrange
    sequence = [3, 1, 2]

    # Act
    result = select_(sequence, str)

    # Assert
    assert result == ["3", "1", "2"]


def test_select_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = select_(sequence, double)

    # Assert
    assert result == []


def test_select_many_flattens_projected_lists():
    # Arrange
    sequence = [1, 2]

    # Act
    result = select_many_(sequence, lambda x: [x, x * 10])

    # Assert
    assert result == [1, 10, 2, 20]


def test_select_many_flattens_only_one_level():
    # Arrange
    sequence = [1, 2]

    # Act
    result = select_many_(sequence, lambda x: [[x]])

    # Assert
    assert result == [[1], [2]]


def test_select_many_skips_empty_inner_lists():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = select_many_(sequence, lambda x: [x] if is_even(x) else [])

    # Assert
    assert result == [2]


def test_select_many_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[int] = []

    # Act
    result = select_many_(sequence, lambda x: [x])

    # Assert
    assert result == []


def test_where_with_index_returns_positions_in_original_list():
    # Arrange
    sequence = [1, 4, 3, 6]

    # Act
    result = where_with_index_(sequence, is_even)

    # Assert
    assert result == {1: 4, 3: 6}


def test_where_with_index_with_no_match_returns_empty_dict():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = where_with_index_(sequence, is_even)

    # Assert
    assert result == {}


def test_where_with_index_on_empty_list_returns_empty_dict():
    # Arrange
    sequence: list[int] = []

    # Act
    result = where_with_index_(sequence, is_even)

    # Assert
    assert result == {}
