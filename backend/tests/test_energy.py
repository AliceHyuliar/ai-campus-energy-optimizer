"""Consumption, credit eligibility, units, and financial rounding boundaries."""

from decimal import Decimal

import pytest

from backend.app.energy import cost_myr, estimate_energy, round_energy
from backend.app.models import DEFAULT_ASSUMPTIONS, EnergyAssumptions, EquipmentState


@pytest.mark.parametrize(
    ("ac_on", "lights_on", "minutes", "expected_kwh", "expected_myr"),
    [
        (True, True, 60, "2.200", "1.10"),
        (True, False, 60, "2.000", "1.00"),
        (False, True, 60, "0.200", "0.10"),
        (False, False, 60, "0.000", "0.00"),
        (True, True, 30, "1.100", "0.55"),
        (True, True, 1, "0.037", "0.02"),
        (True, True, 1440, "52.800", "26.40"),
    ],
)
def test_estimated_consumption_and_full_window_savings(
    ac_on, lights_on, minutes, expected_kwh, expected_myr
):
    result = estimate_energy(
        EquipmentState(ac_on, lights_on),
        minutes,
        Decimal("0.50"),
        DEFAULT_ASSUMPTIONS,
        eligible_for_savings=True,
    )
    assert result.baseline_kwh == Decimal(expected_kwh)
    assert result.potential_savings_kwh == Decimal(expected_kwh)
    assert result.potential_savings_myr == Decimal(expected_myr)


@pytest.mark.parametrize("equipment", [EquipmentState(True, True), EquipmentState(False, True)])
def test_ineligible_rooms_have_consumption_but_no_savings_credit(equipment):
    result = estimate_energy(
        equipment, 60, Decimal("0.50"), DEFAULT_ASSUMPTIONS, eligible_for_savings=False
    )
    assert result.baseline_kwh > 0
    assert result.potential_savings_kwh == 0
    assert result.potential_savings_myr == 0


@pytest.mark.parametrize(
    ("value", "expected"),
    [("0.0004", "0.000"), ("0.0005", "0.001"), ("2.2005", "2.201")],
)
def test_energy_rounds_half_up_to_three_places(value, expected):
    assert round_energy(Decimal(value)) == Decimal(expected)


@pytest.mark.parametrize(
    ("energy", "tariff", "expected"),
    [("0.01", "0.50", "0.01"), ("0.03", "0.50", "0.02"), ("2.2", "0", "0.00")],
)
def test_money_rounds_half_up_to_two_places(energy, tariff, expected):
    assert cost_myr(Decimal(energy), Decimal(tariff)) == Decimal(expected)


def test_assumptions_are_explicit_and_change_calculation_without_a_provider():
    result = estimate_energy(
        EquipmentState(True, True),
        30,
        Decimal("0.75"),
        EnergyAssumptions(Decimal("1.0"), Decimal("0.1"), 15),
        eligible_for_savings=True,
    )
    assert result.baseline_kwh == Decimal("0.550")
    assert result.potential_savings_myr == Decimal("0.41")


@pytest.mark.parametrize("invalid", [Decimal("-1"), Decimal("NaN"), Decimal("Infinity"), 0.5])
def test_invalid_energy_and_tariff_cannot_produce_estimates(invalid):
    with pytest.raises(ValueError):
        round_energy(invalid)
    with pytest.raises(ValueError):
        cost_myr(Decimal("1"), invalid)
    with pytest.raises(ValueError):
        EnergyAssumptions(ac_power_kw=invalid)


@pytest.mark.parametrize("minutes", [0, -1, 1441, True, 1.5])
def test_window_validation(minutes):
    with pytest.raises(ValueError):
        estimate_energy(
            EquipmentState(True, True),
            minutes,
            Decimal("0.50"),
            DEFAULT_ASSUMPTIONS,
            eligible_for_savings=True,
        )


@pytest.mark.parametrize("buffer", [0, 14, 16, True])
def test_preconditioning_semantics_cannot_drift_from_frozen_contract(buffer):
    with pytest.raises(ValueError):
        EnergyAssumptions(preconditioning_minutes=buffer)
