"""
Tests for combat.py — calculate_damage(), NormalDamage, CriticalDamage.
"""
import pytest
from Ironvault.combat import calculate_damage, NormalDamage, CriticalDamage


def test_calculate_damage_returns_correct_value():
    """calculate_damage() returns attack minus defense, floored at 0."""
    assert calculate_damage(30, 10) == 20
    assert calculate_damage(10, 30) == 0
    assert calculate_damage(20, 20) == 0


def test_normal_damage_apply_produces_expected_result(warrior, enemy):
    """NormalDamage.apply() returns calculate_damage(attacker, defender)."""
    strategy = NormalDamage()
    expected = calculate_damage(warrior.effective_attack, enemy.effective_defense)
    assert strategy.apply(warrior, enemy) == pytest.approx(expected, rel=1e-3)


def test_critical_damage_apply_produces_1_5x_normal_damage(warrior, enemy):
    """CriticalDamage.apply() returns 1.5x the normal damage value."""
    normal = NormalDamage()
    critical = CriticalDamage()
    normal_result = normal.apply(warrior, enemy)
    critical_result = critical.apply(warrior, enemy)
    assert critical_result == pytest.approx(normal_result * 1.5, rel=1e-3)