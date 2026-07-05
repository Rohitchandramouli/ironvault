"""
Shared pytest fixtures for IronVault test suite.
"""
import pytest
from Ironvault.items import (
    Weapon, Armour, Accessory, Potion, RepairKit,
    Rarity, BonusType, BrokenItemError
)
from Ironvault.inventory import Inventory
from Ironvault.character import Character, CharacterClass


@pytest.fixture
def common_weapon():
    return Weapon(
        name="Test Sword",
        rarity=Rarity.COMMON,
        attack_power=20,
        max_durability=50,
        durability=50
    )

@pytest.fixture
def broken_weapon():
    return Weapon(
        name="Broken Sword",
        rarity=Rarity.COMMON,
        attack_power=20,
        max_durability=50,
        durability=0
    )

@pytest.fixture
def common_armour():
    return Armour(
        name="Test Armour",
        rarity=Rarity.COMMON,
        defense_rating=15,
        max_durability=50,
        durability=50
    )

@pytest.fixture
def broken_armour():
    return Armour(
        name="Broken Armour",
        rarity=Rarity.COMMON,
        defense_rating=15,
        max_durability=50,
        durability=0
    )

@pytest.fixture
def attack_accessory():
    return Accessory(
        name="Attack Ring",
        rarity=Rarity.COMMON,
        bonus_type=BonusType.ATTACK,
        bonus_percentage=0.10
    )

@pytest.fixture
def defense_accessory():
    return Accessory(
        name="Defense Amulet",
        rarity=Rarity.COMMON,
        bonus_type=BonusType.DEFENSE,
        bonus_percentage=0.10
    )

@pytest.fixture
def potion():
    return Potion(
        name="Health Potion",
        rarity=Rarity.COMMON,
        heal_amount=50
    )

@pytest.fixture
def repair_kit():
    return RepairKit(
        name="Repair Kit",
        rarity=Rarity.COMMON,
        repair_amount=30
    )

@pytest.fixture
def small_inventory():
    """Inventory with very low max_weight for testing InventoryFullError."""
    return Inventory(max_weight=1.0)

@pytest.fixture
def standard_inventory():
    return Inventory(max_weight=100.0)

@pytest.fixture
def warrior():
    return Character(name="Test Warrior", char_class=CharacterClass.EXECUTIONER)

@pytest.fixture
def enemy():
    return Character(name="Test Enemy", char_class=CharacterClass.SENTINEL)