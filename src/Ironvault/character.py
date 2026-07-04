"""
This file contains the character management system for Ironvault.
It defines the `Character` class and its associated methods.
It depends on the `items` module for item definitions and the `inventory` module for inventory management.
It defines the enum, `CharacterClass`, for different character classes.
It only has one class, `Character`, which is used to manage a character's attributes and inventory.
"""

from enum import Enum
import logging
from typing import Any, cast

from Ironvault.items import (
    Item, Gear, Consumable, Rarity, BonusType,
    Weapon, Armour, Accessory, Potion, RepairKit
)

from Ironvault.inventory import Inventory, ItemNotFoundError

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
        self.base_health = self.CLASS_STATS_TABLE[char_class.value]["base_health"]
        self.base_attack = self.CLASS_STATS_TABLE[char_class.value]["base_attack"]
        self.base_defense = self.CLASS_STATS_TABLE[char_class.value]["base_defense"]
        self.health = self.base_health  # now safe — base_health exists
        self.xp_reward_base = self.CLASS_STATS_TABLE[char_class.value]["xp_reward_base"]
        max_weight = self.CLASS_STATS_TABLE[char_class.value]["max_weight"]
        self.inventory = Inventory(max_weight=max_weight)
        self.current_xp = 0
        self.level = 1
        self.equipped_weapon: Weapon | None = None
        self.equipped_armour: Armour | None = None
        self.equipped_accessory: Accessory | None = None

    @property
    def effective_attack(self) -> float:
        """Calculate the effective attack value of the character."""
        bonus = 0
        if self.equipped_weapon and self.equipped_weapon.durability > 0:
            bonus += self.equipped_weapon.attack_power
        if self.equipped_accessory and self.equipped_accessory.bonus_type == BonusType.ATTACK:
            bonus += self.base_attack * self.equipped_accessory.bonus_percentage
        return self.base_attack + bonus

    @property
    def effective_defense(self) -> float:
        """Calculate the effective defense value of the character."""
        bonus = 0
        if self.equipped_armour and self.equipped_armour.durability > 0:
            bonus += self.equipped_armour.defense_rating
        if self.equipped_accessory and self.equipped_accessory.bonus_type == BonusType.DEFENSE:
            bonus += self.base_defense * self.equipped_accessory.bonus_percentage
        return self.base_defense + bonus

    def equip_gear(self,item: Gear) -> None:
        """Equip a gear item to the character."""
        if isinstance(item, Weapon):
            before_attack = self.effective_attack
            if self.equipped_weapon:
                self.equipped_weapon.unequip(self)
            self.equipped_weapon = item
            item.equip(self)
            print(f"[{self.name}] Equipped weapon: {item.name}")
            print(f"[{self.name}] Attack: {before_attack:.0f} → {self.effective_attack:.0f}")
            logger.info("%s equipped weapon: %s. Attack: %.0f → %.0f",
                        self.name, item.name, before_attack, self.effective_attack)
        elif isinstance(item, Armour):
            before_defense = self.effective_defense
            if self.equipped_armour:
                self.equipped_armour.unequip(self)
            self.equipped_armour = item
            item.equip(self)
            print(f"[{self.name}] Equipped armour: {item.name}")
            print(f"[{self.name}] Defense: {before_defense:.0f} → {self.effective_defense:.0f}")
            logger.info("%s equipped armour: %s. Defense: %.0f → %.0f",
                        self.name, item.name, before_defense, self.effective_defense)
        elif isinstance(item, Accessory):
            before_attack = self.effective_attack
            before_defense = self.effective_defense
            if self.equipped_accessory:
                self.equipped_accessory.unequip(self)
            self.equipped_accessory = item
            item.equip(self)
            print(f"[{self.name}] Equipped accessory: {item.name}")
            print(f"[{self.name}] Attack: {before_attack:.0f} → {self.effective_attack:.0f}")
            print(f"[{self.name}] Defense: {before_defense:.0f} → {self.effective_defense:.0f}")
            logger.info("%s equipped accessory: %s. Attack: %.0f → %.0f",
                        self.name, item.name, before_attack, self.effective_attack)
            logger.info("%s equipped accessory: %s. Defense: %.0f → %.0f",
                        self.name, item.name, before_defense, self.effective_defense)
        else:
            logger.warning("%s tried to equip an invalid item: %s", self.name, item.name)

    def unequip_gear(self,item: Gear) -> None:
        """Unequip a gear item from the character."""
        if isinstance(item, Weapon) and self.equipped_weapon:
            before_attack = self.effective_attack
            self.equipped_weapon.unequip(self)
            print(f"[{self.name}] Unequipped weapon: {self.equipped_weapon.name}")
            print(f"[{self.name}] Attack: {before_attack:.0f} → {self.effective_attack:.0f}")
            logger.info("%s unequipped weapon: %s. Attack: %.0f → %.0f",
                        self.name, item.name, before_attack, self.effective_attack)
            self.equipped_weapon = None
        elif isinstance(item, Armour) and self.equipped_armour:
            before_defense = self.effective_defense
            self.equipped_armour.unequip(self)
            print(f"[{self.name}] Unequipped armour: {self.equipped_armour.name}")
            print(f"[{self.name}] Defense: {before_defense:.0f} → {self.effective_defense:.0f}")
            logger.info("%s unequipped armour: %s. Defense: %.0f → %.0f",
                        self.name, item.name, before_defense, self.effective_defense)
            self.equipped_armour = None
        elif isinstance(item, Accessory) and self.equipped_accessory:
            before_attack = self.effective_attack
            before_defense = self.effective_defense
            self.equipped_accessory.unequip(self)
            print(f"[{self.name}] Unequipped accessory: {self.equipped_accessory.name}")
            print(f"[{self.name}] Attack: {before_attack:.0f} → {self.effective_attack:.0f}")
            print(f"[{self.name}] Defense: {before_defense:.0f} → {self.effective_defense:.0f}")
            logger.info("%s unequipped accessory: %s. Attack: %.0f → %.0f",
                        self.name, item.name, before_attack, self.effective_attack)
            logger.info("%s unequipped accessory: %s. Defense: %.0f → %.0f",
                        self.name, item.name, before_defense, self.effective_defense)
            self.equipped_accessory = None
        else:
            logger.warning("%s tried to unequip an invalid or non-equipped item: %s", self.name, item.name)

    def heal(self, amount: int) -> None:
        """Heal the character by a specified amount, without exceeding base health."""
        self.health = min(self.health + amount, self.base_health)

    def use_consumable(self, item:Consumable) -> None:
        """Use a consumable item from the character's inventory."""
        if item not in self.inventory:
            logger.warning("%s tried to use a consumable not in inventory: %s", self.name, item.name)
            raise ItemNotFoundError(f"{item.name} not found in Inventory.")
        item.use(self)
        self.inventory.remove_item(item)
        logger.info("%s used consumable: %s", self.name, item.name)
        if isinstance(item, Potion):
            logger.info("%s health after potion: %d/%d",
                        self.name, self.health, self.base_health)
        elif isinstance(item, RepairKit) and item.selected_target is not None:
            logger.info("Repaired %s. Current durability: %d/%d",
                        item.selected_target.name,
                        item.selected_target.durability,
                        item.selected_target.max_durability)

    def gain_xp(self, amount: int) -> None:
        """Gain experience points and handle leveling up."""
        self.current_xp += amount
        logger.info("%s gained %d XP. Current XP: %d", self.name, amount, self.current_xp)
        while True:
            level_up_threshold = int(self.level * 100 * self.XP_MULTIPLIER)
            if self.current_xp < level_up_threshold:
                break
            self.level+=1
            self.current_xp -= level_up_threshold
            self.base_health += int(self.base_health * 0.1)  # Increase base health by 10%
            self.base_attack += int(self.base_attack * 0.1)  # Increase base attack by 10%
            self.base_defense += int(self.base_defense * 0.1)  # Increase base defense by 10%
            self.health = self.base_health  # Restore health to new max
            logger.info("%s leveled up! New level: %d, Base Health: %d, Base Attack: %d, Base Defense: %d",
                        self.name, self.level, self.base_health, self.base_attack, self.base_defense)
        logger.info("%s's current XP after processing: %d", self.name, self.current_xp)

    def to_dict(self) -> dict[str, Any]:
        """Convert the character's state to a dictionary for serialization."""
        return {
            "name": self.name,
            "char_class": self.char_class.value,
            "level": self.level,
            "current_xp": self.current_xp,
            "health": self.health,
            "xp_reward_base": self.xp_reward_base,
            "base_health": self.base_health,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "equipped_weapon": self.equipped_weapon.to_dict() if self.equipped_weapon else None,
            "equipped_armour": self.equipped_armour.to_dict() if self.equipped_armour else None,
            "equipped_accessory": self.equipped_accessory.to_dict() if self.equipped_accessory else None,
            "inventory": self.inventory.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Character":
        """Create a Character instance from a dictionary."""
        char_class = CharacterClass(data["char_class"])
        character = cls(name=data["name"], char_class=char_class)
        character.level = data["level"]
        character.current_xp = data["current_xp"]
        character.health = data["health"]
        character.xp_reward_base = data["xp_reward_base"]
        character.base_health = data["base_health"]
        character.base_attack = data["base_attack"]
        character.base_defense = data["base_defense"]
        character.inventory = Inventory.from_dict(data["inventory"])

        # Equip items if they exist
        if data.get("equipped_weapon"):
            weapon_data = data["equipped_weapon"]
            character.equipped_weapon = cast(Weapon, Item.from_dict(weapon_data))
            character.equipped_weapon.equip(character)

        if data.get("equipped_armour"):
            armour_data = data["equipped_armour"]
            character.equipped_armour = cast(Armour, Item.from_dict(armour_data))
            character.equipped_armour.equip(character)

        if data.get("equipped_accessory"):
            accessory_data = data["equipped_accessory"]
            character.equipped_accessory = cast(Accessory, Item.from_dict(accessory_data))
            character.equipped_accessory.equip(character)

        return character