"""
Tests for items.py — item hierarchy, use(), degrade(), from_dict(), to_dict().
"""
import pytest
from typing import cast
from unittest.mock import MagicMock
from Ironvault.items import (
    Item, Weapon, Armour, Accessory, Potion, RepairKit,
    Rarity, BonusType, BrokenItemError
)


def test_weapon_use_raises_broken_item_error_at_zero_durability(broken_weapon):
    """Weapon.use() raises BrokenItemError when durability is 0."""
    mock_character = MagicMock()
    with pytest.raises(BrokenItemError):
        broken_weapon.use(mock_character)


def test_armour_use_raises_broken_item_error_at_zero_durability(broken_armour):
    """Armour.use() raises BrokenItemError when durability is 0."""
    mock_character = MagicMock()
    with pytest.raises(BrokenItemError):
        broken_armour.use(mock_character)


def test_weapon_degrade_reduces_durability(common_weapon):
    """Weapon.degrade() reduces durability by expected percentage amount."""
    initial_durability = common_weapon.durability
    common_weapon.degrade()
    expected_decay = max(1, int(initial_durability * 0.05))
    assert common_weapon.durability == initial_durability - expected_decay


def test_potion_use_calls_character_heal(potion):
    """Potion.use() calls character.heal() with the correct heal_amount."""
    mock_character = MagicMock()
    potion.use(mock_character)
    mock_character.heal.assert_called_once_with(potion.heal_amount)


def test_item_from_dict_constructs_correct_subclass():
    """Item.from_dict() constructs the correct subclass from the type field."""
    weapon_dict = {
        "type": "Weapon",
        "name": "Test Sword",
        "rarity": "COMMON",
        "weight": 2.5,
        "attack_power": 20,
        "max_durability": 50,
        "durability": 50,
        "is_equipped": False
    }
    item = Item.from_dict(weapon_dict)
    assert isinstance(item, Weapon)
    assert item.name == "Test Sword"
    assert item.attack_power == 20
    assert item.durability == 50


def test_item_to_dict_from_dict_round_trips_correctly(common_weapon):
    """Item.to_dict() / from_dict() preserves all attributes exactly."""
    original_dict = common_weapon.to_dict()
    reconstructed = cast(Weapon, Item.from_dict(original_dict))
    assert reconstructed.name == common_weapon.name
    assert reconstructed.rarity == common_weapon.rarity
    assert reconstructed.attack_power == common_weapon.attack_power
    assert reconstructed.durability == common_weapon.durability
    assert reconstructed.max_durability == common_weapon.max_durability