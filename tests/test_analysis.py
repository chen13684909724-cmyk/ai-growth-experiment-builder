from pathlib import Path

import pandas as pd

from analysis import demo_data, load_data, minimum_sample_size, segment_performance, two_proportion_test


def fixture_df():
    return pd.DataFrame(
        {
            "user id": range(1, 9),
            "test group": ["ad"] * 4 + ["psa"] * 4,
            "converted": [1, 1, 0, 1, 0, 0, 1, 0],
            "total ads": [3, 8, 21, 120, 2, 9, 35, 105],
            "most ads day": ["Monday"] * 8,
            "most ads hour": [10, 11, 12, 13, 10, 11, 12, 13],
        }
    )


def test_lift_direction():
    result = two_proportion_test(fixture_df())
    assert result.treatment_rate == 0.75
    assert result.control_rate == 0.25
    assert result.absolute_lift == 0.5


def test_segment_rows_exist():
    result = segment_performance(fixture_df(), "exposure band")
    assert not result.empty
    assert "absolute_lift" in result.columns


def test_sample_size_is_positive():
    assert minimum_sample_size(0.03, 0.15) > 0


def test_real_dataset_schema():
    data = Path(__file__).parents[1] / "data" / "marketing_AB.csv"
    if data.exists():
        assert len(load_data(data)) == 588101


def test_public_demo_schema():
    df = demo_data()
    assert len(df) == 12000
    assert set(df["test group"]) == {"ad", "psa"}
