import spinq.dicts
import spinq.lists


def test_spinq_resolves_to_local_workspace_source():
    # Arrange
    module_path = spinq.lists.__file__

    # Act
    is_local_source = "site-packages" not in module_path.replace("\\", "/")

    # Assert
    assert is_local_source, f"spinq resolved to {module_path}, not workspace source"


def test_lists_module_exposes_every_documented_helper():
    # Arrange
    expected = {
        "first_",
        "first_or_none_",
        "first_or_none_with_index_",
        "last_",
        "last_or_none_",
        "single_",
        "single_or_none_",
        "filter_",
        "except_",
        "without_",
        "union_",
        "select_",
        "select_many_",
        "where_",
        "where_with_index_",
        "distinct_",
        "order_by_",
        "order_by_descending_",
        "any_",
        "all_",
        "none_",
    }

    # Act
    actual = {name for name in vars(spinq.lists) if name.endswith("_")}

    # Assert
    assert expected <= actual


def test_dicts_module_exposes_every_documented_helper():
    # Arrange
    expected = {
        "first_",
        "first_or_none_",
        "get_key_by_index_",
        "get_key_value_by_index_",
    }

    # Act
    actual = {name for name in vars(spinq.dicts) if name.endswith("_")}

    # Assert
    assert expected <= actual
