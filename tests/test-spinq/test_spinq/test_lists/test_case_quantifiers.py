from spinq.lists import all_, any_, none_


def is_even(value: int) -> bool:
    return value % 2 == 0


def test_any_returns_true_when_one_element_matches():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = any_(sequence, is_even)

    # Assert
    assert result is True


def test_any_returns_false_when_no_element_matches():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = any_(sequence, is_even)

    # Assert
    assert result is False


def test_any_on_empty_list_returns_false():
    # Arrange
    sequence: list[int] = []

    # Act
    result = any_(sequence, is_even)

    # Assert
    assert result is False


def test_all_returns_true_when_every_element_matches():
    # Arrange
    sequence = [2, 4, 6]

    # Act
    result = all_(sequence, is_even)

    # Assert
    assert result is True


def test_all_returns_false_when_one_element_does_not_match():
    # Arrange
    sequence = [2, 3, 6]

    # Act
    result = all_(sequence, is_even)

    # Assert
    assert result is False


def test_all_on_empty_list_returns_true():
    # Arrange
    sequence: list[int] = []

    # Act
    result = all_(sequence, is_even)

    # Assert
    assert result is True


def test_none_returns_true_when_no_element_matches():
    # Arrange
    sequence = [1, 3, 5]

    # Act
    result = none_(sequence, is_even)

    # Assert
    assert result is True


def test_none_returns_false_when_one_element_matches():
    # Arrange
    sequence = [1, 2, 3]

    # Act
    result = none_(sequence, is_even)

    # Assert
    assert result is False


def test_none_on_empty_list_returns_true():
    # Arrange
    sequence: list[int] = []

    # Act
    result = none_(sequence, is_even)

    # Assert
    assert result is True
