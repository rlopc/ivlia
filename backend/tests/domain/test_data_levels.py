from ivlia.domain.data_policy.levels import DataLevel


def test_levels_are_ordered_by_sensitivity() -> None:
    assert DataLevel.PUBLIC < DataLevel.INTERNAL < DataLevel.PRIVATE < DataLevel.SECRET


def test_derived_data_takes_the_highest_level() -> None:
    assert max(DataLevel.INTERNAL, DataLevel.PRIVATE) is DataLevel.PRIVATE
