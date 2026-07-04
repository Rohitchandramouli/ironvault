"""
This module contains the inventory management system for Ironvault.
It only deals with the inventory of a character, allowing them to add, remove, and manage items.
It depends only on the `items` module for item definitions.
It only has one class, `Inventory`, which is used to manage a character's inventory.
"""

import logging
from random import randint, choice
from typing import TYPE_CHECKING, Any, Generator

from Ironvault.items import (
    Item, Gear, Consumable, Rarity, BonusType,
    Weapon, Armour, Accessory, Potion, RepairKit
)

if TYPE_CHECKING:
    from Ironvault.character import Character

logger = logging.getLogger(__name__)

ITEM_NAMES = {
    Weapon: {
        Rarity.COMMON: [
            # 15 Items - Massive baseline pool
            "Rusty Greatsword", "Chipped Cleaver", "Bent Arming Sword", "Dented Mace",
            "Crude Estoc", "Worn Flanged Mace", "Blunt Executioner's Blade", "Splintered Spear",
            "Notched Hatchet", "Rusted Claymore", "Fractured Warhammer", "Dulled Dirk",
            "Pitted Falchion", "Battered Morningstar", "Warped Quarterstaff"
        ],
        Rarity.UNCOMMON: [
            # 12 Items - Significant pool
            "Heavy Iron Cleaver", "Steel Greataxe", "Weighted Spiked Club", "Barbed Poleaxe",
            "Polished Broadsword", "Standard Arming Sword", "Steel Flail", "Cavalry Lance",
            "Balanced Long dagger", "Huntsman's Hatchet", "Spiked Morningstar", "Tempered Falchion"
        ],
        Rarity.RARE: [
            # 8 Items - Specialized pool
            "Beheader's Crescent", "Colossal Maul", "War-Forged Greatsword", "Gore-Spike Mace",
            "Masterwork Rapier", "Folded Steel Longsword", "Vanguard War-Pick", "Starlight Estoc"
        ],
        Rarity.EPIC: [
            # 6 Items - Elite pool
            "Doom-Herald Decapitator", "Blood-Feast Crescent", "Void-Forged Greataxe",
            "Bone-Crusher Sledge", "Silverwing Sabre", "Aegis-Breaker Lance"
        ],
        Rarity.LEGENDARY: [
            # 4 Items - Highly exclusive artifacts
            "Worldsplitter Greatsword", "Soulreaper Crescent",
            "Dawnbreaker Rapier", "The Sovereign Sentinel Longsword"
        ]
    },
    Armour: {
        Rarity.COMMON: [
            # 15 Items
            "Tattered Garb", "Scrap-Metal Plate Pieces", "Moth-Eaten Tunic", "Rusty Mail Links",
            "Dented Cuirass", "Threadbare Cloth Jerkin", "Cracked Hauberk", "Sooted Blacksmith Apron",
            "patched Leather Coat", "Brittle Iron Scale Vest", "Frayed Padded Doublet", "Stained Robes",
            "Ripped Gambeson", "Corroded Breastplate", "Torn Outcast Shroud"
        ],
        Rarity.UNCOMMON: [
            # 12 Items
            "Iron Plate Harness", "Soldier's Polished Cuirass", "Reinforced Mail Breastplate",
            "Hardened Pit-Fighter Leather", "Boar-Hide Vest", "Thick Cloth Wraps", "Sturdy Chain Shirt",
            "Studded Gambeson", "Watchman's Mail Hauberk", "Brigand's Hide Vest", "Standard Steel Plate",
            "Thickened Leather Jerkin"
        ],
        Rarity.RARE: [
            # 8 Items
            "Bastion Iron Clad", "Fortress Juggernaut Mail", "Obsidian Wall Armor",
            "Duelist's Gilded Brigandine", "Royal Guard Finemail", "Berserker's Fur Harness",
            "Gladiator's Leather Pauldrons", "Flayed-Hide Bracers"
        ],
        Rarity.EPIC: [
            # 6 Items
            "Dreadnought Mountain Carapace", "Stalwart Vanguard Greatplate", "Titan-Steel Bulk",
            "Wind-Weaver Silk Armor", "Quicksilver Masterwork Mail", "Executioner's Shroud"
        ],
        Rarity.LEGENDARY: [
            # 4 Items
            "Aegis of the Unmovable Fortress", "The God-King's Living Wall",
            "Celestial Shroud of Flawless Parry", "Apocalypse Slaughter-Garb"
        ]
    },
    Accessory: {
        Rarity.COMMON: [
            # 12 Items - Smaller base due to accessory type size constraints
            "Copper Band", "String Charm", "Dull Locket", "Bone Ring", "Frayed Sash", "Plain Ring",
            "Tarnished Brooch", "Lead Signet", "Rope Necklace", "Chipped Bead Amulet",
            "Crude Bone Pendant", "Dull Brass Ring"
        ],
        Rarity.UNCOMMON: [
            # 9 Items
            "Brawler's Brass Knuckles", "Slayer's Crimson Ring", "Sharpened Flint Pendant",
            "Sturdy Iron Signet", "Heavy Steel Torc", "Thick Leather Belt",
            "Polished Amber Band", "Silver Locket", "Engraved Bone Charm"
        ],
        Rarity.RARE: [
            # 7 Items
            "Heart-Stone Pendant", "Berserker's Blood-Band", "Grip of the Bear Gauntlets",
            "Guardian's Runic Ring", "Deflective Jade Talisman", "Vanguard Cloak Pins",
            "Starlight Choker"
        ],
        Rarity.EPIC: [
            # 5 Items
            "Doom-Infused Locket", "Vampiric Onyx Choker", "Giant-Slayer's Girdle",
            "Aegis Star Compass", "Glacial Heart Talisman"
        ],
        Rarity.LEGENDARY: [
            # 3 Items
            "The One True Slaughter Band", "Heart of the Raging Volcano Amulet",
            "The Undying Bastion Emblem"
        ]
    },
    Potion:
            ["Health Potion"],
    RepairKit:
            ["Repair Kit"]
}


class InventoryFullError(RuntimeError):
    """Raised when the inventory is full."""
    pass

class ItemNotFoundError(RuntimeError):
    """Raised when an item is not found in the inventory."""
    pass

class Inventory:
    """Class representing a character's inventory."""
    def __init__(self, max_weight: float) -> None:
        self._gear: list[Gear] = []
        self._consumables: list[Consumable] = []
        self.max_weight = max_weight

    @property
    def gear(self) -> list[Gear]:
        """Returns a list of gear items in the inventory."""
        return self._gear.copy()

    @property
    def consumables(self) -> list[Consumable]:
        """Returns a list of consumable items in the inventory."""
        return self._consumables.copy()

    @property
    def total_weight(self) -> float:
        """Returns the total weight of all items in the inventory."""
        return sum(item.weight for item in self._gear + self._consumables)

    def __len__(self) -> int:
        """Returns the total number of items in the inventory."""
        return len(self._gear) + len(self._consumables)

    def __contains__(self, item: Item) -> bool:
        """Checks if an item is in the inventory."""
        return item in self._gear or item in self._consumables

    def __iter__(self) -> Generator[Item, None, None]:
        """Returns an iterator over all items in the inventory."""
        yield from self._gear
        yield from self._consumables

    def __repr__(self) -> str:
        """Returns a string representation of the inventory."""
        return f"Inventory(items={len(self)}, weight={self.total_weight:.2f}/{self.max_weight:.2f}kg)"

    def add_item(self, item: Item) -> None:
        """Adds an item to the inventory if it doesn't exceed max weight."""
        if self.total_weight + item.weight > self.max_weight:
            logger.warning("Cannot add %s: inventory would exceed max weight.", item.name)
            raise InventoryFullError(f"Cannot add {item.name}: inventory would exceed max weight.")
        if isinstance(item, Gear):
            self._gear.append(item)
        elif isinstance(item, Consumable):
            self._consumables.append(item)
        else:
            logger.error("Attempted to add an item of invalid type: %s", type(item).__name__)
            raise TypeError("Item must be of type Gear or Consumable.")
        logger.info("Added %s to inventory.", item.name)

    def remove_item(self, item: Item) -> None:
        """Removes an item from the inventory."""
        if isinstance(item, Gear):
            try:
                self._gear.remove(item)
            except ValueError:
                logger.warning("Attempted to remove %s, but it was not found in gear.", item.name)
                raise ItemNotFoundError(f"{item.name} not found in Inventory.")
        elif isinstance(item, Consumable):
            try:
                self._consumables.remove(item)
            except ValueError:
                logger.warning("Attempted to remove %s, but it was not found in consumables.", item.name)
                raise ItemNotFoundError(f"{item.name} not found in Inventory.")
        else:
            logger.error("Attempted to remove an item of invalid type: %s", type(item).__name__)
            raise TypeError("Item must be of type Gear or Consumable.")
        logger.info("Removed %s from inventory.", item.name)

    def equip(self, gear: Gear, character: "Character") -> None:
        """Equips a gear item to the character."""
        if gear not in self._gear:
            logger.warning("Attempted to equip %s, but it is not in Inventory.", gear.name)
            raise ItemNotFoundError(f"{gear.name} not found in Inventory.")
        character.equip_gear(gear)
        logger.info("Equipped %s to character.", gear.name)

    def unequip(self, gear: Gear, character: "Character") -> None:
        """Unequips a gear item from the character."""
        if gear not in self._gear:
            logger.warning("Attempted to unequip %s, but it is not in Inventory.", gear.name)
            raise ItemNotFoundError(f"{gear.name} not found in Inventory.")
        character.unequip_gear(gear)
        logger.info("Unequipped %s from character.", gear.name)

    def loot_drop(self) -> Generator[Item, None, None]:
        """Generates a random loot drop."""
        item_types = [Weapon, Armour, Accessory, Potion, RepairKit]
        rarities = list(Rarity)
        for _ in range(randint(1, 5)):  # Random number of items
            item_class = choice(item_types)
            rarity = choice(rarities)
            if item_class is Weapon:
                name = choice(ITEM_NAMES[Weapon][rarity])
                yield Weapon(name=name, rarity=rarity)
            elif item_class is Armour:
                name = choice(ITEM_NAMES[Armour][rarity])
                yield Armour(name=name, rarity=rarity)
            elif item_class is Accessory:
                name = choice(ITEM_NAMES[Accessory][rarity])
                bonus_type = choice(list(BonusType))
                yield Accessory(name=name, rarity=rarity, bonus_type=bonus_type)
            elif item_class is Potion:
                name = choice(ITEM_NAMES[Potion])
                yield Potion(name=name, rarity=rarity, heal_amount=50)
            elif item_class is RepairKit:
                name = choice(ITEM_NAMES[RepairKit])
                yield RepairKit(name=name, rarity=rarity, repair_amount=30)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the inventory to a dictionary."""
        return {
            "max_weight": self.max_weight,
            "gear": [item.to_dict() for item in self._gear],
            "consumables": [item.to_dict() for item in self._consumables]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Inventory":
        """Deserializes the inventory from a dictionary."""
        inventory = cls(max_weight=data["max_weight"])
        for item_data in data["gear"]:
            item = Item.from_dict(item_data)
            inventory.add_item(item)
        for item_data in data["consumables"]:
            item = Item.from_dict(item_data)
            inventory.add_item(item)
        return inventory