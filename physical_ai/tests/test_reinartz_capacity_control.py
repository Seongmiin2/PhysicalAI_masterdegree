from src.experiments.reinartz_capacity_control import HIDDEN_DIM, parameter_count
from src.models.reinartz_forecaster import GRUForecaster


def test_f0_c_parameter_count_is_close_to_f1() -> None:
    f0_c = parameter_count()
    f1 = sum(parameter.numel() for parameter in GRUForecaster(52, 64, 1).parameters())
    assert HIDDEN_DIM == 68
    assert f0_c == 25_473
    assert abs(f0_c - f1) / f1 < 0.01
