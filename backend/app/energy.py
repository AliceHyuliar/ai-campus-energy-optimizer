"""Pure Decimal-based estimates using explicit kW, minutes, and MYR/kWh inputs."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from backend.app.models import (
    EnergyAssumptions,
    EquipmentState,
    require_decimal,
    require_integer,
)


def round_energy(value: Decimal) -> Decimal:
    require_decimal("energy", value)
    return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def cost_myr(energy_kwh: Decimal, tariff_myr_per_kwh: Decimal) -> Decimal:
    require_decimal("energy_kwh", energy_kwh)
    require_decimal("tariff_myr_per_kwh", tariff_myr_per_kwh)
    return (energy_kwh * tariff_myr_per_kwh).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class EnergyEstimate:
    baseline_kwh: Decimal
    potential_savings_kwh: Decimal
    potential_savings_myr: Decimal


def estimate_energy(
    equipment: EquipmentState,
    window_minutes: int,
    tariff_myr_per_kwh: Decimal,
    assumptions: EnergyAssumptions,
    *,
    eligible_for_savings: bool,
) -> EnergyEstimate:
    require_integer("window_minutes", window_minutes, 1, 1440)
    require_decimal("tariff_myr_per_kwh", tariff_myr_per_kwh)
    if type(eligible_for_savings) is not bool:
        raise ValueError("Savings eligibility must be boolean")
    power_kw = (assumptions.ac_power_kw if equipment.ac_on else Decimal(0)) + (
        assumptions.lighting_power_kw if equipment.lights_on else Decimal(0)
    )
    baseline = round_energy(power_kw * Decimal(window_minutes) / Decimal(60))
    savings = baseline if eligible_for_savings else Decimal("0.000")
    # Cost is calculated from the rounded energy returned in the public snapshot.
    return EnergyEstimate(baseline, savings, cost_myr(savings, tariff_myr_per_kwh))
