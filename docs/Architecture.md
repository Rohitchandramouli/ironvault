# Architecture

Detailed module reference for IronVault. For design reasoning, see [Engineering-Decisions.md](Engineering-Decisions.md).

---

## Dependency Direction

```
items.py → inventory.py → character.py → combat.py → main.py
```

No file imports from anything above it in the chain. This is enforced structurally — if any module needed to import upward, it would indicate a design problem, not a missing import.

---

## `items.py` — What things are

Foundation of the dependency chain. No imports from any other IronVault module.

### Enums

**`Rarity`**

| Shorthand | Full Name |
|-----------|-----------|
| C | Common |
| UC | Uncommon |
| R | Rare |
| E | Epic |
| L | Legendary |

Each member stores both shorthand and full name via a custom `__init__` — accessible as `rarity.shorthand` and `rarity.fullname`.

**`BonusType`**

`ATTACK` · `DEFENSE` · `HEALTH`

String values (`"Attack"`, `"Defense"`, `"Health"`) serve as keys into `Accessory.BONUS_RANGES` and are serialized directly in `to_dict()`.

### Item Hierarchy

```
Item (abstract)
├── Gear (abstract)
│   ├── Weapon       — attack_power, durability, max_durability
│   ├── Armour       — defense_rating, durability, max_durability
│   └── Accessory    — bonus_type, bonus_percentage
└── Consumable (abstract)
    ├── Potion       — heal_amount (fixed, not rarity-scaled)
    └── RepairKit    — repair_amount (fixed), selected_target set by caller
```

### Rarity Scaling

Weapon and Armour stats are randomly generated from rarity-scaled ranges at creation time:

| Rarity | Stat Range | Durability Range |
|--------|-----------|-----------------|
| Common | 10–30 | 1–20 |
| Uncommon | 31–60 | 21–40 |
| Rare | 61–90 | 41–60 |
| Epic | 91–120 | 61–80 |
| Legendary | 121–150 | 81–100 |

`Weapon` and `Armour` share the same durability range (`Gear.DURABILITY_RANGES`) and the same stat range (`Gear.STAT_RANGES`). This keeps attack and defense balanced for the subtraction damage formula — `damage = attack - defense`.

Accessory bonus percentages are rarity-scaled per `BonusType`:

| Rarity | ATTACK / DEFENSE | HEALTH |
|--------|-----------------|--------|
| Common | 1–5% | 2–8% |
| Uncommon | 6–10% | 9–15% |
| Rare | 11–18% | 16–25% |
| Epic | 19–25% | 26–35% |
| Legendary | 26–40% | 36–50% |

Health scales wider because a percentage health bonus needs to feel meaningful relative to the base health pool.

### Weight Ranges

Weight is a physical property of the item type, not a power property. Not rarity-scaled. Each subclass defines its own range:

| Type | Weight Range |
|------|-------------|
| Weapon | 1.0–5.0 kg |
| Armour | 5.0–25.0 kg |
| Accessory | 0.1–0.5 kg |
| Potion | 0.2–0.5 kg |
| RepairKit | 2.0–6.0 kg |

### `Item.from_dict()` — Factory Classmethod

All item construction flows through this single classmethod. It reads `data["type"]` to determine the subclass, reconstructs `Rarity` from `data["rarity"]` via `Rarity[name]`, and passes all saved stats as optional parameters so values are restored exactly rather than rerolled.

```python
Item.from_dict({"type": "Weapon", "name": "Iron Blade", "rarity": "UNCOMMON", ...})
# Returns a fully reconstructed Weapon instance
```

### Custom Exceptions

`BrokenItemError` — raised by `Weapon.use()` and `Armour.use()` when `durability == 0`. Inherits from `RuntimeError`.

---

## `inventory.py` — Who owns what

Imports from `items.py` only.

### Internal Structure

```python
_gear: list[Gear]           # private — only accessible via .gear property
_consumables: list[Consumable]  # private — only accessible via .consumables property
max_weight: float
```

`gear` and `consumables` are properties returning copies of the internal lists. External code cannot mutate them directly — all modifications go through `add_item()` and `remove_item()`.

### Dunder Methods

| Dunder | Behavior |
|--------|----------|
| `__len__` | `len(_gear) + len(_consumables)` |
| `__contains__` | Checks both lists — `item in inventory` works naturally |
| `__iter__` | Yields gear first, then consumables |
| `__repr__` | `Inventory(items=N, weight=X.XX/Y.YYkg)` |

### `loot_drop()` Generator

```python
for item in inventory.loot_drop():
    try:
        inventory.add_item(item)
    except InventoryFullError:
        break
```

Yields between 1 and 5 items per call. Picks a random concrete subclass and rarity each iteration. Has no side effects — it yields items but never adds them. The caller decides what to do with each one, including whether to handle `InventoryFullError` mid-loop.

Item names are drawn from a curated pool per type per rarity tier. The pool sizes follow a pyramid structure — 15 Common weapon names, 4 Legendary weapon names — so higher-rarity items feel rarer by name distinctiveness, not just stats.

### Custom Exceptions

- `InventoryFullError` — raised by `add_item()` when `total_weight + item.weight > max_weight`
- `ItemNotFoundError` — raised by `remove_item()` when the item is not in either list

---

## `character.py` — Who acts

Imports from `items.py` and `inventory.py`.

### `CharacterClass` — Starting Stats

| Class | Health | Attack | Defense | Max Weight | XP Reward Base |
|-------|--------|--------|---------|------------|----------------|
| Sentinel | 150 | 15 | 45 | 45 kg | 120 |
| Executioner | 80 | 50 | 5 | 25 kg | 100 |
| Gladiator | 160 | 35 | 15 | 35 kg | 110 |
| Champion | 95 | 25 | 40 | 30 kg | 105 |

These values live in `Character.CLASS_STATS_TABLE` — a class variable shared across all instances. `Character.__init__` looks up the correct row at creation time.

Class identity is flavor-only for equipment — a Sentinel can equip zero armour if the player chooses. Restrictions were explicitly deferred.

### Effective Stats

```python
@property
def effective_attack(self) -> float:
    bonus: float = 0.0
    if self.equipped_weapon and self.equipped_weapon.durability > 0:
        bonus += self.equipped_weapon.attack_power
    if self.equipped_accessory and self.equipped_accessory.bonus_type == BonusType.ATTACK:
        bonus += self.base_attack * self.equipped_accessory.bonus_percentage
    return self.base_attack + bonus
```

Accessory bonus applies to `base_attack` only — not to the already-equipment-modified effective stat. This makes equip order irrelevant. Broken gear (durability == 0) silently contributes nothing. The item stays equipped and visible but acts as if absent.

### Level-Up

`XP_MULTIPLIER = 1.5` is a class variable. Level-up threshold: `int(level * 100 * XP_MULTIPLIER)`.

On level-up:
- `level` increments
- `base_health`, `base_attack`, `base_defense` each increase by 10% (`int(stat * 0.1)`)
- `health` restores to new `base_health`
- Excess XP carries over to the next level

### `Character` as both Player and Enemy

There is no separate `Enemy` class. Both the player character and any enemy are `Character` instances. `combat()` operates only against the `Character` interface. This avoids duplicating logic and mirrors how real game engines handle entity identity.

### Serialization

`to_dict()` serializes all instance state including equipped items as full dicts. `from_dict()` reconstructs via `Item.from_dict()` for each equipped item, using `cast()` to satisfy static analysis since `Item.from_dict()` returns `Item` not a specific subclass.

---

## `combat.py` — What happens between them

Imports from `character.py` only.

### Strategy Pattern

```python
class DamageStrategy(ABC):
    @abstractmethod
    def apply(self, attacker: Character, defender: Character) -> float:
        pass

class NormalDamage(DamageStrategy):
    def apply(self, attacker, defender):
        return calculate_damage(attacker.effective_attack, defender.effective_defense)

class CriticalDamage(DamageStrategy):
    def apply(self, attacker, defender):
        return calculate_damage(attacker.effective_attack, defender.effective_defense) * 1.5
```

`combat()` accepts a `strategy` parameter defaulting to `NormalDamage()`. New damage types require only a new strategy class — the turn loop never changes.

### `calculate_damage()`

```python
def calculate_damage(attack: float, defense: float) -> float:
    return max(0.0, attack - defense)
```

Module-level pure function. Takes two numbers, returns a number. No knowledge of characters, items, or game state. Originally designed as a `@staticmethod` — made a module-level function during implementation since it has no natural class to belong to.

### Turn Structure

```
char_a attacks char_b
  → damage applied (clamped to 0, cast to int)
  → char_a's weapon degrades if equipped and durability > 0
  → char_a's armour degrades if equipped and durability > 0
  → if weapon just broke: print bare-fisted notification (once)
  → if armour just broke: print unarmoured notification (once)
  → log attack result
  → if char_b.health == 0: break (no death strike back)

char_b attacks char_a
  → same sequence
```

`turn_count` increments after each individual attack — two increments per full round.

### `CombatResult`

```python
@dataclass
class CombatResult:
    winner: Character
    defeated: Character
    turn_count: int
    final_health: dict[str, int]
```

---

## `main.py` — How it all fits together

Imports from all four modules. No game logic — only orchestration.

### Functions

| Function | Responsibility |
|----------|---------------|
| `save_game(character, filename)` | `json.dump` via context manager |
| `load_game(filename)` | `json.load` → `Character.from_dict()`, raises `CorruptSaveError` |
| `show_character_status(character)` | Print current state to terminal |
| `loot_room(character, source_inventory, header)` | Iterate `loot_drop()`, player picks up items one by one |
| `equip_menu(character)` | Numbered gear list, player selects, calls `equip_gear()` |
| `consumable_menu(character)` | Numbered consumable list, handles `RepairKit` target selection |
| `fight_enemy(character)` | Spawn random enemy, run `combat()`, award XP and loot |
| `game_loop(character)` | Repeating options menu |
| `run()` | Entry point — logging config, opening menu, calls `game_loop()` |

### Logging Configuration

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    handlers=[logging.FileHandler("logs/ironvault.log", encoding="utf-8")]
)
```

All internal system events go to `logs/ironvault.log`. Terminal output is reserved for player-facing narrative only.

### Custom Exceptions

`CorruptSaveError` — raised by `load_game()` on `json.JSONDecodeError`, missing keys, or file not found. Inherits from `RuntimeError`.

---

## Public API

`src/Ironvault/__init__.py` exposes the full engine surface using explicit re-export syntax:

```python
from Ironvault.items import Item as Item, Weapon as Weapon, ...
from Ironvault.inventory import Inventory as Inventory, ...
from Ironvault.character import Character as Character, CharacterClass as CharacterClass
from Ironvault.combat import combat as combat, CombatResult as CombatResult, ...
```

`Name as Name` syntax is the Python standard for intentional re-exports — it signals "this import is public API" rather than an accidental unused import that linters would flag.
