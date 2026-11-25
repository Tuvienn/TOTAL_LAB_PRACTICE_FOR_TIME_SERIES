import numpy as np
import pytest

from practice_1.analysis import compute_acf_table, generate_white_noise


def test_white_noise_matches_approved_contract() -> None:
    series = generate_white_noise(
        size=1000,
        seed=42,
        mean=0.0,
        standard_deviation=1.0,
    )

    assert len(series) == 1000
    assert series.name == "white_noise"
    assert series.mean() == pytest.approx(-0.028891550995946837)
    assert series.std(ddof=1) == pytest.approx(0.9892170876543358)

    repeated = generate_white_noise(size=1000, seed=42)
    assert np.array_equal(series.to_numpy(), repeated.to_numpy())

    acf_table = compute_acf_table(series, max_lag=40, alpha=0.05)
    assert acf_table["lag"].tolist() == list(range(41))
    assert acf_table.loc[1, "acf"] == pytest.approx(0.08705487216529355)
    assert acf_table[["acf", "lower_ci", "upper_ci"]].notna().all().all()


def test_white_noise_does_not_change_numpy_global_random_state() -> None:
    np.random.seed(123)
    expected = np.random.random(4)

    np.random.seed(123)
    generate_white_noise(size=10, seed=42)
    actual = np.random.random(4)

    assert np.array_equal(actual, expected)


@pytest.mark.parametrize(
    ("kwargs", "error_type"),
    [
        ({"size": 0}, ValueError),
        ({"size": -1}, ValueError),
        ({"size": 2.5}, TypeError),
        ({"size": True}, TypeError),
        ({"mean": np.inf}, ValueError),
        ({"standard_deviation": 0.0}, ValueError),
        ({"standard_deviation": -1.0}, ValueError),
        ({"standard_deviation": np.nan}, ValueError),
    ],
)
def test_white_noise_rejects_invalid_parameters(
    kwargs: dict[str, object],
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        generate_white_noise(**kwargs)
