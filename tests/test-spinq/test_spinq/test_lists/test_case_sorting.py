from spinq.lists import order_by_, order_by_descending_


def by_rank(pair: tuple[str, int]) -> int:
    return pair[1]


def test_order_by_sorts_by_key_selector_not_by_element():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    result = order_by_(sequence, by_rank)

    # Assert
    assert result == [("a", 1), ("c", 2), ("b", 3)]


def test_order_by_descending_sorts_by_key_selector_not_by_element():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    result = order_by_descending_(sequence, by_rank)

    # Assert
    assert result == [("b", 3), ("c", 2), ("a", 1)]


def test_order_by_descending_is_reverse_of_order_by():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    ascending = order_by_(sequence, by_rank)
    descending = order_by_descending_(sequence, by_rank)

    # Assert
    assert descending == list(reversed(ascending))


def test_order_by_does_not_mutate_input():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    order_by_(sequence, by_rank)

    # Assert
    assert sequence == [("b", 3), ("a", 1), ("c", 2)]


def test_order_by_descending_does_not_mutate_input():
    # Arrange
    sequence = [("b", 3), ("a", 1), ("c", 2)]

    # Act
    order_by_descending_(sequence, by_rank)

    # Assert
    assert sequence == [("b", 3), ("a", 1), ("c", 2)]


def test_order_by_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[tuple[str, int]] = []

    # Act
    result = order_by_(sequence, by_rank)

    # Assert
    assert result == []


def test_order_by_descending_on_empty_list_returns_empty_list():
    # Arrange
    sequence: list[tuple[str, int]] = []

    # Act
    result = order_by_descending_(sequence, by_rank)

    # Assert
    assert result == []
