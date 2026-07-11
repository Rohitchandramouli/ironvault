# Architecture

> How IronVault is structured, what each module owns, and how the pieces connect.

---

## The Core Principle

Every module has exactly one responsibility. Dependencies flow in one direction only — no file imports from anything above it in the chain.

```
items.py  →  inventory.py  →  character.py  →  combat.py  →  main.py
```

This was decided before implementation began. The result: every module is independently importable, testable, and replaceable.

---

## Module Map

| Module | Owns | Imports from |
|--------|------|-------------|
| `items.py` | Everything that can exist in the game world | Nothing internal |
| `inventory.py` | Everything about owning and managing items | `items.py` |
| `character.py` | Everything about who acts and how they progress | `items.py`, `inventory.py` |
| `combat.py` | Everything about what happens between characters | `character.py` |
| `main.py` | Orchestration, save/load, player interface | Everything |

---

## `items.py` — What Things Are

The foundation. No internal imports.

### The Hierarchy

```
Item  (abstract)
│
├── Gear  (abstract — equippable, has is_equipped flag)
│   ├── Weapon      attack_power + durability, both rarity-scaled
│   ├── Armour      defense_rating + durability, both rarity-scaled
│   └── Accessory   bonus_type + bonus_percentage, rarity-scaled per type
│
└── Consumable  (abstract — use() returns True, signals removal)
    ├── Potion      heal_amount (fixed value, not rarity-scaled)
    └── RepairKit   repair_amount (fixed value), selected_target set by caller
```

### Enums

**`Rarity`** — each member stores both shorthand and full name

| Member | Shorthand | Full Name |
|--------|-----------|-----------|
| COMMON | C | Common |
| UNCOMMON | UC | Uncommon |
| RARE | R | Rare |
| EPIC | E | Epic |
| LEGENDARY | L | Legendary |

**`BonusType`** — `ATTACK` · `DEFENSE` · `HEALTH`

### Rarity Scaling Tables

Weapon and Armour share the same stat ranges — keeping attack and defense balanced for the `damage = attack - defense` formula.

| Rarity | Stat Range | Durability Range |
|--------|-----------|-----------------|
| Common | 10–30 | 1–20 |
| Uncommon | 31–60 | 21–40 |
| Rare | 61–90 | 41–60 |
| Epic | 91–120 | 61–80 |
| Legendary | 121–150 | 81–100 |

Accessory bonus percentages scale per `BonusType`. Health scales wider because a percentage bonus needs to feel meaningful against a large HP pool.

| Rarity | ATTACK / DEFENSE | HEALTH |
|--------|-----------------|--------|
| Common | 1–5% | 2–8% |
| Uncommon | 6–10% | 9–15% |
| Rare | 11–18% | 16–25% |
| Epic | 19–25% | 26–35% |
| Legendary | 26–40% | 36–50% |

### Weight Ranges

Weight is a physical property of the item type — not rarity-scaled. A Legendary potion isn't heavier than a Common one.

| Type | Range |
|------|-------|
| Weapon | 1.0–5.0 kg |
| Armour | 5.0–25.0 kg |
| Accessory | 0.1–0.5 kg |
| Potion | 0.2–0.5 kg |
| RepairKit | 2.0–6.0 kg |

### `Item.from_dict()` — The Factory

All item construction flows through this single classmethod. Whether the caller is `loot_drop()`, `load_game()`, or `Character.from_dict()` — one place handles it.

```python
# Reads "type" to determine subclass
# Reads "rarity" to reconstruct the Rarity enum member
# Passes all saved stats as optional params — values restored exactly, not rerolled
Item.from_dict({"type": "Weapon", "name": "Iron Blade", "rarity": "UNCOMMON", ...})
```

### Custom Exceptions

`BrokenItemError` — raised by `Weapon.use()` and `Armour.use()` when `durability == 0`.

---

## `inventory.py` — Who Owns What

Manages item ownership, weight limits, and loot generation.

### Internal Structure

```python
_gear: list[Gear]             # private
_consumables: list[Consumable] # private

gear        # property → returns a copy, never the live list
consumables # property → returns a copy, never the live list
total_weight # property → computed fresh, never stored
```

External code cannot mutate the internal lists directly. All modifications go through `add_item()` and `remove_item()`.

### The Dunder Interface

`Inventory` behaves like a native Python container:

```python
len(inventory)          # __len__  — combined count across both lists
item in inventory       # __contains__ — checks both lists
for item in inventory:  # __iter__ — gear first, then consumables
repr(inventory)         # __repr__ — Inventory(items=3, weight=12.50/30.00kg)
```

### `loot_drop()` — How Loot Works

```python
for item in inventory.loot_drop():
    try:
        inventory.add_item(item)
    except InventoryFullError:
        break  # bag full mid-loot — stop looting
```

- Yields 1–5 items per call
- Picks a random concrete subclass and rarity each iteration
- Has **no side effects** — yields items, never adds them
- The caller decides what to do with each one

Item names are drawn from a curated pool per type per rarity tier. Pool sizes follow a pyramid — 15 Common weapon names, 4 Legendary weapon names — so Legendary items feel rare by name distinctiveness, not just stats.

### Custom Exceptions

| Exception | Raised by | When |
|-----------|-----------|------|
| `InventoryFullError` | `add_item()` | `total_weight + item.weight > max_weight` |
| `ItemNotFoundError` | `remove_item()` | Item not in either list |

---

## `character.py` — Who Acts

The core agent. Owns an `Inventory` by composition.

### Character Classes

| Class | Health | Attack | Defense | Max Weight | XP Reward |
|-------|--------|--------|---------|------------|-----------|
| Sentinel | 150 | 15 | 45 | 45 kg | 120 |
| Executioner | 80 | 50 | 5 | 25 kg | 100 |
| Gladiator | 160 | 35 | 15 | 35 kg | 110 |
| Champion | 95 | 25 | 40 | 30 kg | 105 |

These live in `Character.CLASS_STATS_TABLE` — a class variable shared across all instances. Equipment restrictions are **flavor only** — a Sentinel can equip zero armour if the player chooses.

### Effective Stats — How They're Calculated

```
effective_attack  =  base_attack
                  +  (base_attack × accessory_bonus%)   ← if ATTACK accessory equipped
                  +  weapon.attack_power                 ← if weapon equipped and durability > 0

effective_defense =  base_defense
                  +  (base_defense × accessory_bonus%)  ← if DEFENSE accessory equipped
                  +  armour.defense_rating              ← if armour equipped and durability > 0
```

Key rules:
- Accessory bonus applies to **base stat only** — not the equipment-modified value. Makes equip order irrelevant.
- Broken gear (durability == 0) silently contributes nothing. The item stays visible but acts as absent.
- Both are `@property` — always correct by construction, never stored.

### Level-Up

```
threshold = level × 100 × 1.5
```

On crossing the threshold:
- `level` increments
- `base_health`, `base_attack`, `base_defense` each grow by 10%
- `health` restores to new `base_health`
- Excess XP carries over

### One Class, Two Roles

There is no separate `Enemy` class. Both the player and any enemy are `Character` instances. `combat()` operates only against the `Character` interface — it never checks which one is the player.

### Custom Exceptions

None directly. Raises `ItemNotFoundError` (from `inventory.py`) in `use_consumable()` if the item isn't in inventory.

---

## `combat.py` — What Happens Between Them

### Strategy Pattern

```python
strategy = NormalDamage()   # or CriticalDamage(), or any future strategy
result = combat(player, enemy, strategy)
```

| Strategy | Behavior |
|----------|----------|
| `NormalDamage` | `max(0, attacker.effective_attack - defender.effective_defense)` |
| `CriticalDamage` | Normal damage × 1.5 |

Adding new damage types requires only a new class inheriting from `DamageStrategy`. The turn loop never changes.

### Turn Structure

```
char_a attacks char_b
  → damage applied, health clamped to 0
  → char_a's weapon degrades (if equipped and durability > 0)
  → char_a's armour degrades (if equipped and durability > 0)
  → if weapon just broke → print "fights bare-fisted!" (once only)
  → if armour just broke → print "is unarmoured!" (once only)
  → log and print attack result

if char_b.health == 0 → break (no death strike allowed)

char_b attacks char_a
  → same sequence
```

### Return Value

```python
@dataclass
class CombatResult:
    winner: Character
    defeated: Character
    turn_count: int
    final_health: dict[str, int]
```

---

## `main.py` — How It All Fits Together

Orchestration only. No game logic.

### Function Responsibilities

| Function | Does |
|----------|------|
| `save_game(character, filename)` | `json.dump` via context manager |
| `load_game(filename)` | `json.load` → `Character.from_dict()`, raises `CorruptSaveError` on bad data |
| `show_character_status(character)` | Print current state to terminal |
| `loot_room(character, source, header)` | Iterate `loot_drop()`, player picks up items one by one |
| `equip_menu(character)` | Numbered gear list, player selects, calls `equip_gear()` |
| `consumable_menu(character)` | Consumable list, handles `RepairKit` target selection |
| `fight_enemy(character)` | Spawn random enemy, run `combat()`, award XP and loot |
| `game_loop(character)` | Repeating options menu — the core game loop |
| `run()` | Console entry point — logging config, opening menu |

### Logging

All internal events go to `logs/ironvault.log`. Terminal output is reserved for player-facing narrative only. The two concerns are never mixed.

```python
logging.basicConfig(
    handlers=[logging.FileHandler("logs/ironvault.log", encoding="utf-8")]
)
```

### Custom Exceptions

`CorruptSaveError` — raised by `load_game()` on malformed JSON, missing fields, or file not found.

---

## Public API

`src/Ironvault/__init__.py` exposes the full engine using explicit re-export syntax:

```python
from Ironvault.items import Weapon as Weapon, Rarity as Rarity, ...
from Ironvault.inventory import Inventory as Inventory, ...
from Ironvault.character import Character as Character, CharacterClass as CharacterClass
from Ironvault.combat import combat as combat, CombatResult as CombatResult, ...
```

`Name as Name` is the Python standard for intentional public re-exports — it tells linters "this import is deliberate" rather than flagging it as unused.

---

*For the reasoning behind these structural choices, see [Engineering-Decisions.md](Engineering-Decisions.md).*
