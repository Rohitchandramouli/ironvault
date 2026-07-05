"""
Tests for character.py — effective stats, equip/unequip, gain_xp(), level-up.
"""
import pytest
from Ironvault.character import Character, CharacterClass
from Ironvault.items import BonusType


def test_effective_attack_includes_weapon_bonus_when_durability_positive(
    warrior, common_weapon
):
    """effective_attack adds weapon.attack_power when durability > 0."""
    warrior.inventory.add_item(common_weapon)
    warrior.equip_gear(common_weapon)
    expected = warrior.base_attack + common_weapon.attack_power
    assert warrior.effective_attack == pytest.approx(expected, rel=1e-3)


def test_effective_attack_excludes_weapon_bonus_when_durability_zero(
    warrior, broken_weapon
):
    """effective_attack falls back to base_attack when weapon durability is 0."""
    warrior.inventory.add_item(broken_weapon)
    warrior.equip_gear(broken_weapon)
    assert warrior.effective_attack == warrior.base_attack


def test_effective_defense_includes_armour_bonus_when_durability_positive(
    warrior, common_armour
):
    """effective_defense adds armour.defense_rating when durability > 0."""
    warrior.inventory.add_item(common_armour)
    warrior.equip_gear(common_armour)
    expected = warrior.base_defense + common_armour.defense_rating
    assert warrior.effective_defense == pytest.approx(expected, rel=1e-3)


def test_effective_defense_excludes_armour_bonus_when_durability_zero(
    warrior, broken_armour
):
    """effective_defense falls back to base_defense when armour durability is 0."""
    warrior.inventory.add_item(broken_armour)
    warrior.equip_gear(broken_armour)
    assert warrior.effective_defense == warrior.base_defense


def test_attack_accessory_bonus_applies_correctly(warrior, attack_accessory):
    """ATTACK accessory bonus correctly increases effective_attack."""
    warrior.inventory.add_item(attack_accessory)
    warrior.equip_gear(attack_accessory)
    expected = warrior.base_attack + (warrior.base_attack * attack_accessory.bonus_percentage)
    assert warrior.effective_attack == pytest.approx(expected, rel=1e-3)


def test_defense_accessory_bonus_applies_correctly(warrior, defense_accessory):
    """DEFENSE accessory bonus correctly increases effective_defense."""
    warrior.inventory.add_item(defense_accessory)
    warrior.equip_gear(defense_accessory)
    expected = warrior.base_defense + (warrior.base_defense * defense_accessory.bonus_percentage)
    assert warrior.effective_defense == pytest.approx(expected, rel=1e-3)


def test_gain_xp_increments_level_when_threshold_crossed(warrior):
    """gain_xp() increments level when current_xp reaches level_up_threshold."""
    threshold = warrior.level_up_threshold
    warrior.gain_xp(threshold)
    assert warrior.level == 2


def test_level_up_applies_flat_percentage_stat_increase(warrior):
    """Level-up increases base_health, base_attack, base_defense by 10%."""
    initial_health = warrior.base_health
    initial_attack = warrior.base_attack
    initial_defense = warrior.base_defense
    threshold = warrior.level_up_threshold
    warrior.gain_xp(threshold)
    assert warrior.base_health == initial_health + int(initial_health * 0.1)
    assert warrior.base_attack == initial_attack + int(initial_attack * 0.1)
    assert warrior.base_defense == initial_defense + int(initial_defense * 0.1)