"""
This file contains the character management system for Ironvault.
It defines the `Character` class and its associated methods.
It depends on the `items` module for item definitions and the `inventory` module for inventory management.
It defines the enum, `CharacterClass`, for different character classes.
It only has one class, `Character`, which is used to manage a character's attributes and inventory.
"""

from enum import Enum
import logging
from typing import Any

from Ironvault.items import (
    Item, Gear, Consumable, Rarity, BonusType,
    Weapon, Armour, Accessory, Potion, RepairKit
)

from Ironvault.inventory import Inventory

logger = logging.getLogger(__name__)

class CharacterClass(Enum):
    """Enum representing the core playable combat archetypes."""
    SENTINEL = "SENTINEL"       # Unmovable frontline, heaviest plate
    EXECUTIONER = "EXECUTIONER" # Glass cannon, massive two-handed weapon, zero armor
    GLADIATOR = "GLADIATOR"     # Brawler, raw health pool, trades wounds freely
    CHAMPION = "CHAMPION"       # Duelist, masterwork armor, near-impossible to hit
class Character:
    """Class representing a character in Ironvault."""

    CLASS_STATS_TABLE = {
        "SENTINEL": {
            "base_health": 150,     # Heaviest frontline survivability
            "base_attack": 15,      # Low single-target threat
            "base_defense": 45,     # Highest native mitigation
            "max_weight": 45.0,     # High capacity to bear the heaviest plate
            "xp_reward_base": 120   # Worth more XP to defeat due to high tankiness
        },
        "EXECUTIONER": {
            "base_health": 80,      # Fragile glass cannon pool
            "base_attack": 50,      # Highest native offense for two-handed swings
            "base_defense": 5,      # Zero native armor armor tier
            "max_weight": 25.0,     # Lower capacity; only needs to carry a massive weapon
            "xp_reward_base": 100
        },
        "GLADIATOR": {
            "base_health": 160,     # Highest raw health pool; trades wounds freely
            "base_attack": 35,      # Solid brawler offense
            "base_defense": 15,     # Low native armor; relies heavily on high health
            "max_weight": 35.0,     # Moderate capacity for raw brawler gear
            "xp_reward_base": 110
        },
        "CHAMPION": {
            "base_health": 95,      # Lower duelist health pool
            "base_attack": 25,      # Moderate, precise offense
            "base_defense": 40,     # Near-impossible to hit; high native mitigation
            "max_weight": 30.0,     # Tuned perfectly for masterwork armor sets
            "xp_reward_base": 105
        }
    }

    # Shared level-up threshold scaling across all Characters
    XP_MULTIPLIER = 1.5

    def __init__(self, name: str, char_class: CharacterClass) -> None:
        self.name = name
        self.char_class = char_class
        self.level = 1
        self.xp = 0
        max_weight = self.CLASS_STATS_TABLE[char_class.value]["max_weight"]
        self.inventory = Inventory(max_weight=max_weight)
        self.base_health = self.CLASS_STATS_TABLE[char_class.value]["base_health"]
        self.base_attack = self.CLASS_STATS_TABLE[char_class.value]["base_attack"]
        self.base_defense = self.CLASS_STATS_TABLE[char_class.value]["base_defense"]
        self.health = self.base_health
        self.equipped_weapon: Weapon | None = None
        self.equipped_armour: Armour | None = None
        self.equipped_accessory: Accessory | None = None