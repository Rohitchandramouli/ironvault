"""
IronVault public API.
Exposes the core classes, enums, exceptions, and functions of the IronVault
turn-based RPG engine as a unified package interface.
Importers can access all engine functionality via `from Ironvault import ...`
without needing to know the internal module structure.
"""

from Ironvault.items import (
    Item, Gear, Weapon, Armour, Accessory,
    Consumable, Potion, RepairKit,
    Rarity, BonusType,
    BrokenItemError
)
from Ironvault.inventory import Inventory, InventoryFullError, ItemNotFoundError
from Ironvault.character import Character, CharacterClass
from Ironvault.combat import combat, CombatResult, DamageStrategy, NormalDamage, CriticalDamage

# CorruptSaveError imported from main.py once implemented