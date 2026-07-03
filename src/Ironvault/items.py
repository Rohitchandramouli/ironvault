"""
This module contains the base class and subclasses for all items in the game.
It is completely independent of the rest of the game code.So this module has no internal dependencies and serves as the foundation of the IronVault engine.
It contains 3 abstract classes: Item, Gear and Consumable.Gear contains 3 subclasses: Weapon, Armour and Accessory. Consumable contains 2 subclasses: Potion and Repair Kit.
"""

from abc import ABC, abstractmethod
from enum import Enum
import logging
from random import randint, uniform

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from Ironvault.character import Character

logger = logging.getLogger(__name__)

class BrokenItemError(RuntimeError):
    """Raised when a Weapon or Armour is used with durability at zero."""
    pass

class Rarity(Enum):
    """Enum for the different rarities of items."""
    COMMON = ("C", "Common")
    UNCOMMON = ("UC", "Uncommon")
    RARE = ("R", "Rare")
    EPIC = ("E", "Epic")
    LEGENDARY = ("L", "Legendary")

    def __init__(self, shorthand:str, fullname:str) -> None:
        self.shorthand = shorthand
        self.fullname = fullname

class BonusType(Enum):
    """Enum for the different types of bonuses that can be applied to items."""
    ATTACK = "Attack"
    DEFENSE = "Defense"
    HEALTH = "Health"

class Item(ABC):
    """Abstract base class for all items in the game."""
    def __init__(self, name:str, rarity:Rarity, weight:float) -> None:
        self.name = name
        self.rarity = rarity
        self.weight = weight

    @abstractmethod
    def use(self, character: "Character") -> bool | None:
        pass

    @abstractmethod
    def degrade(self) -> None:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Item":
        """Load item attributes from a dictionary."""
        item_type = data["type"]
        rarity = Rarity[data["rarity"]]
        if item_type == "Weapon":
            return Weapon(
                name=data["name"],
                rarity=rarity,
                weight=data["weight"],
                attack_power=data["attack_power"],
                max_durability=data["max_durability"],
                durability=data["durability"]
            )
        elif item_type == "Armour":
            return Armour(
                name=data["name"],
                rarity=rarity,
                weight=data["weight"],
                defense_rating=data["defense_rating"],
                max_durability=data["max_durability"],
                durability=data["durability"]
            )
        elif item_type == "Accessory":
            bonus_type = BonusType(data["bonus_type"])
            accessory = Accessory(
                name=data["name"],
                rarity=rarity,
                weight=data["weight"],
                bonus_type=bonus_type
            )
            accessory.bonus_percentage = data["bonus_percentage"]
            return accessory
        elif item_type == "Potion":
            return Potion(
                name=data["name"],
                rarity=rarity,
                weight=data["weight"],
                heal_amount=data["heal_amount"]
            )
        elif item_type == "RepairKit":
            return RepairKit(
                name=data["name"],
                rarity=rarity,
                weight=data["weight"],
                repair_amount=data["repair_amount"]
            )
        else:
            raise ValueError(f"Unknown item type: {item_type}")

class Gear(Item):
    """Abstract base class for all gear items in the game."""

    DURABILITY_RANGES = {
    Rarity.COMMON: (1, 20),
    Rarity.UNCOMMON: (21, 40),
    Rarity.RARE: (41, 60),
    Rarity.EPIC: (61, 80),
    Rarity.LEGENDARY: (81, 100)
    }

    STAT_RANGES = {
    Rarity.COMMON: (10, 30),
    Rarity.UNCOMMON: (31, 60),
    Rarity.RARE: (61, 90),
    Rarity.EPIC: (91, 120),
    Rarity.LEGENDARY: (121, 150)
    }

    def __init__(self,name:str, rarity:Rarity, weight:float) -> None:
        super().__init__(name, rarity, weight)
        self.is_equipped = False

    def equip(self, character: "Character") -> None:
        """Equip the gear item."""
        self.is_equipped = True

    def unequip(self, character: "Character") -> None:
        """Unequip the gear item from the character."""
        self.is_equipped = False

class Weapon(Gear):
    """Class representing a weapon item."""

    def __init__(self, name:str, rarity:Rarity, weight:float, attack_power: int | None =None, max_durability: int | None = None, durability: int | None = None) -> None:
        super().__init__(name, rarity, weight)
        self.attack_power = attack_power if attack_power is not None else randint(*self.STAT_RANGES[rarity])
        self.max_durability = max_durability if max_durability is not None else randint(*self.DURABILITY_RANGES.get(rarity, (0, 0)))
        self.durability = durability if durability is not None else self.max_durability

    def use(self, character: "Character") -> None:
        """Use the weapon to attack an enemy."""
        if self.durability <= 0:
            logger.warning("%s is broken and cannot be used.", self.name)
            raise BrokenItemError(f"{self.name} is broken and cannot be used.")
        self.degrade()

    def degrade(self) -> None:
        """Calculate decay as a percentage of total durability (e.g., ~5% per use).
        Higher quality items naturally yield a lower fraction relative to usage"""
        decay_amount = max(1, int(self.durability * 0.05))

        self.durability = max(0, self.durability - decay_amount)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "Weapon",
            "name": self.name,
            "rarity": self.rarity.name,
            "weight": self.weight,
            "attack_power": self.attack_power,
            "max_durability": self.max_durability,
            "durability": self.durability,
            "is_equipped": self.is_equipped
        }

class Armour(Gear):
    """Class representing a armour item."""

    def __init__(self, name:str, rarity:Rarity, weight:float, defense_rating: int | None = None, max_durability: int | None = None, durability: int | None = None) -> None:
        super().__init__(name, rarity, weight)
        self.defense_rating = defense_rating if defense_rating is not None else randint(*self.STAT_RANGES[rarity])
        self.max_durability = max_durability if max_durability is not None else randint(*self.DURABILITY_RANGES.get(rarity, (0, 0)))
        self.durability = durability if durability is not None else self.max_durability

    def use(self, character: "Character") -> None:
        """Use the armour to protect the character."""
        if self.durability <= 0:
            logger.warning("%s is broken and cannot be used.", self.name)
            raise BrokenItemError(f"{self.name} is broken and cannot be used.")
        self.degrade()

    def degrade(self) -> None:
        """Calculate decay as a percentage of total durability (e.g., ~5% per use).
        Higher quality items naturally yield a lower fraction relative to usage"""
        decay_amount = max(1, int(self.durability * 0.05))

        self.durability = max(0, self.durability - decay_amount)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "Armour",
            "name": self.name,
            "rarity": self.rarity.name,
            "weight": self.weight,
            "defense_rating": self.defense_rating,
            "max_durability": self.max_durability,
            "durability": self.durability,
            "is_equipped": self.is_equipped
        }

class Accessory(Gear):
    """Class representing a accessory item."""

    BONUS_RANGES = {
        "ATTACK": {
            Rarity.COMMON: (0.01, 0.05),     # +1% to +5%
            Rarity.UNCOMMON: (0.06, 0.10),   # +6% to +10%
            Rarity.RARE: (0.11, 0.18),       # +11% to +18%
            Rarity.EPIC: (0.19, 0.25),       # +19% to +25%
            Rarity.LEGENDARY: (0.26, 0.40)   # +26% to +40%
        },
        "DEFENSE": {
            Rarity.COMMON: (0.01, 0.05),
            Rarity.UNCOMMON: (0.06, 0.10),
            Rarity.RARE: (0.11, 0.18),
            Rarity.EPIC: (0.19, 0.25),
            Rarity.LEGENDARY: (0.26, 0.40)
        },
        "HEALTH": {
            Rarity.COMMON: (0.02, 0.08),     # Health scales wider to feel impactful
            Rarity.UNCOMMON: (0.09, 0.15),
            Rarity.RARE: (0.16, 0.25),
            Rarity.EPIC: (0.26, 0.35),
            Rarity.LEGENDARY: (0.36, 0.50)   # Max +50% base health
        }
    }

    def __init__(self, name: str, rarity: Rarity, weight: float, bonus_type: BonusType, bonus_percentage: float | None = None) -> None:
        super().__init__(name, rarity, weight)
        self.bonus_type = bonus_type
        #  Look up the ranges via the self. class variable reference
        type_ranges = self.BONUS_RANGES.get(self.bonus_type.value, {})
        min_max_tuple = type_ranges.get(self.rarity, (0.0, 0.0))

        # Unpack (*) into uniform for the float calculation
        self.bonus_percentage =bonus_percentage if bonus_percentage is not None else round(uniform(*min_max_tuple), 3)

    def use(self, character: "Character") -> None:
        """Accessories are passive — their bonus is applied via Character properties, not through use()."""
        pass


    def degrade(self) -> None:
        """Accessories do not degrade in this implementation."""
        pass

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "Accessory",
            "name": self.name,
            "rarity": self.rarity.name,
            "weight": self.weight,
            "bonus_type": self.bonus_type.value,
            "bonus_percentage": self.bonus_percentage,
            "is_equipped": self.is_equipped
        }

class Consumable(Item):
    """Abstract base class for all consumable items in the game."""

    def __init__(self, name:str, rarity:Rarity, weight:float) -> None:
        super().__init__(name, rarity, weight)

    @abstractmethod
    def use(self, character: "Character") -> bool :
        """Use the consumable item."""
        pass

class Potion(Consumable):
    """Class representing a potion item."""

    def __init__(self, name:str,rarity:Rarity, weight:float, heal_amount:int) -> None:
        super().__init__(name, rarity, weight)
        self.heal_amount = heal_amount

    def use(self, character: "Character") -> bool:
        """Use the potion to restore health."""
        character.heal(self.heal_amount)
        return True

    def degrade(self) -> None:
        """Potions do not degrade in this implementation."""
        pass

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "Potion",
            "name": self.name,
            "rarity": self.rarity.name,
            "weight": self.weight,
            "heal_amount": self.heal_amount
        }

class RepairKit(Consumable):
    """Class representing a repair kit item."""

    def __init__(self, name:str, rarity:Rarity, weight:float, repair_amount:int) -> None:
        super().__init__(name, rarity, weight)
        self.repair_amount = repair_amount
        self.selected_target: Weapon | Armour | None = None

    def use(self, character: "Character") -> bool:
        """Use the repair kit to restore durability of gear."""
        if self.selected_target is not None:
            self.selected_target.durability = min(
                self.selected_target.durability + self.repair_amount,
                self.selected_target.max_durability
            )
        return True

    def degrade(self) -> None:
        """Repair kits do not degrade in this implementation."""
        pass

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "RepairKit",
            "name": self.name,
            "rarity": self.rarity.name,
            "weight": self.weight,
            "repair_amount": self.repair_amount
        }
