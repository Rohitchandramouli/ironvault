"""
IronVault public API.
Exposes the core classes, enums, exceptions, and functions of the IronVault turn-based RPG engine as a unified package interface.
Importers can access all engine functionality via `from Ironvault import ...` without needing to know the internal module structure.
"""

from Ironvault.items import (
    Item as Item,
    Gear as Gear,
    Weapon as Weapon,
    Armour as Armour,
    Accessory as Accessory,
    Consumable as Consumable,
    Potion as Potion,
    RepairKit as RepairKit,
    Rarity as Rarity,
    BonusType as BonusType,
    BrokenItemError as BrokenItemError,
)
from Ironvault.inventory import (
    Inventory as Inventory,
    InventoryFullError as InventoryFullError,
    ItemNotFoundError as ItemNotFoundError,
)
from Ironvault.character import (
    Character as Character,
    CharacterClass as CharacterClass,
)
from Ironvault.combat import (
    combat as combat,
    CombatResult as CombatResult,
    DamageStrategy as DamageStrategy,
    NormalDamage as NormalDamage,
    CriticalDamage as CriticalDamage,
)