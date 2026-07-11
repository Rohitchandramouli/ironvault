# Engineering Decisions

> Every decision in IronVault was made before implementation began. This document records what was decided, why, and what changed during the build — and why those changes were made too.

---

## How to Read This Document

The decisions are organized in two layers:

1. **Original design decisions** — the 27 architectural choices locked in before a single line of code was written
2. **Implementation decisions** — what changed during the build, and why

Both matter. The original decisions show how the system was designed. The implementation decisions show what reality looked like when design met code.

---

## Original Design Decisions

### Structural Decisions

---

**1 — One-way dependency direction**

`items.py → inventory.py → character.py → combat.py → main.py`

No file imports from anything above it in the chain. This was enforced as a constraint before implementation began — not discovered through refactoring.

*Why it matters:* Every module can be imported, tested, and reasoned about in isolation. If `items.py` needed to know about `Character`, that would be a design problem, not a missing import.

---

**2 — Composition over inheritance for `Character`**

`Character` *has* an `Inventory`. It does not extend one.

*Why it matters:* Inheritance would mean every `Character` method also inherits every `Inventory` method — a fragile coupling that makes the class harder to reason about. Composition keeps responsibilities cleanly separated: `Character` is an agent, `Inventory` is a container.

---

**3 — Abstract base classes over duck typing**

`Item`, `Gear`, `Consumable`, and `DamageStrategy` are all abstract. You cannot instantiate them directly.

*Why it matters:* The contracts here — every `Item` must implement `use()`, `degrade()`, and `to_dict()` — need to fail at class definition time, not at runtime when a missing method causes an unexpected `AttributeError` mid-combat.

---

**4 — `Character` serves as both player and enemy**

There is no separate `Enemy` class. Both the player and any enemy are `Character` instances.

*Why it matters:* `combat()` operates only against the `Character` interface. This avoids duplicating logic and mirrors how real game engines handle entity identity — a Sentinel enemy and a Sentinel player are the same class with different names.

---

**5 — Single equipment slot per gear type**

One weapon slot, one armour slot, one accessory slot. Equipping a new item unequips the previous occupant automatically.

*Why it matters:* Dual-wielding would require slot tracking, conflict resolution, and more complex effective stat calculations. Deferred deliberately — the architecture supports it with minimal changes when ready.

---

### Item Design Decisions

---

**6 — `Item` is lean by design**

`Item` only defines what is genuinely true of every single item without exception: `name`, `rarity`, `weight`, and three abstract method contracts.

*Why it matters:* A generic shared `condition` field that all subclasses reinterpret was explicitly rejected. It would crowd the base class with state that only some subclasses use — exactly the kind of thing that makes inheritance hierarchies confusing to navigate.

---

**7 — `Gear` exists purely for equip/unequip behavior**

`Gear` does not hold `durability`. That lives on `Weapon` and `Armour` individually, because `Accessory` has no durability concept.

*Why it matters:* Adding durability to `Gear` would force `Accessory` to carry a field it never uses — the same crowding problem avoided in `Item`.

---

**8 — `degrade()` is abstract on `Item` even for `Accessory`**

`Accessory.degrade()` is a deliberate no-op. But it must be implemented.

*Why it matters:* Making it abstract signals that every item in this world has a lifecycle, even if some choose not to act on it. It's a design statement, not just a method.

---

**9 — `use()` contract is uniform, with one justified exception**

Every item's `use()` takes `character` as its only parameter. `RepairKit` is the single exception — it adds `select_target()` as a separate method called *before* `use()`, rather than breaking the uniform signature.

*Why it matters:* `combat()` and `use_consumable()` can call `item.use(character)` on any item without type-checking. The polymorphic contract stays intact. `RepairKit` just has an additional method beyond the shared contract — subclasses are allowed to do more than the base requires.

---

**10 — `Consumable` signals its own removal via return value**

`Consumable.use()` returns `True` to tell the caller "remove me from inventory."

*Why it matters:* The alternative — having the item hold a back-reference to its `Inventory` and remove itself — would create a dependency from `items.py` upward to `inventory.py`, violating the one-way dependency direction. A return value signal keeps the chain intact.

---

**11 — Rarity scales stats, not weight**

Weight is a physical property of what an item *is*. A Legendary potion is not heavier than a Common one.

*Why it matters:* Conflating power with weight would make the game feel arbitrary. A warrior who can't carry a Legendary sword because it's too heavy, despite the sword being functionally better, doesn't make physical sense.

---

**12 — `Item.from_dict()` as single construction point**

All item construction — from `loot_drop()`, from `load_game()`, from `Character.from_dict()` — flows through one classmethod factory.

*Why it matters:* If construction logic lived in each callsite, changes to how items are built would require finding and updating multiple places. One change propagates everywhere automatically.

---

### Inventory Design Decisions

---

**13 — Internal lists are private, properties return copies**

`_gear` and `_consumables` are never exposed directly. The `gear` and `consumables` properties return copies.

*Why it matters:* If external code could do `inventory._gear.append(item)`, it would bypass the weight check in `add_item()` completely. Returning copies makes the violation obvious — appending to a copy does nothing to the real list.

---

**14 — Equipped items stay in inventory**

When gear is equipped, it stays in `_gear` with `is_equipped = True`. It was not moved to a separate holder on `Character`.

*Why it matters:* Two structures tracking the same items would be a synchronization bug waiting to happen. One source of truth, always. `total_weight` correctly includes worn gear because it sums the actual inventory.

---

**15 — `loot_drop()` has no side effects**

The generator yields items and does nothing else. It never calls `add_item()`.

*Why it matters:* "Generating loot" and "managing inventory capacity" are separate concerns. The caller decides what to do with each yielded item — including stopping mid-loot when the bag fills. This also means the same generator works for dungeon rooms and post-combat enemy drops without any changes.

---

### Character Design Decisions

---

**16 — Accessory bonus applies to base stat only**

The accessory percentage is applied to `base_attack` or `base_defense`, not to the effective value after weapon/armour bonuses are added.

*Why it matters:* If the bonus applied to the already-modified effective stat, equip order would matter — equipping the weapon first would give a different result than equipping the accessory first. Base-stat-only makes the calculation order-independent. Same result, any sequence.

---

**17 — Broken gear silently degrades stats, not crashes combat**

When durability hits zero, `effective_attack` and `effective_defense` silently exclude the broken item's bonus. The item stays equipped. `BrokenItemError` only fires if `use()` is called directly on a broken item.

*Why it matters:* A crash mid-combat would be a terrible player experience. Silent degradation is realistic — a broken sword still exists, it just doesn't contribute. The player sees a notification the turn it breaks, then combat continues.

---

**18 — `CharacterClass` sets starting stats only**

Class identity determines starting values. It does not restrict equipment choices or change how stats are calculated.

*Why it matters:* Equipment restrictions add complexity to `equip_gear()` with limited gameplay payoff at this stage. The class identity comes through clearly enough from starting stat distribution — a Sentinel is tankier than an Executioner from turn one, regardless of what they equip.

---

### Combat Design Decisions

---

**19 — Strategy pattern for damage**

`DamageStrategy` with `NormalDamage` and `CriticalDamage` means `combat()`'s turn loop never changes when new damage types are added. Only new strategy classes are written.

*Why it matters:* This is the Open/Closed Principle in practice. Adding `PoisonDamage` or `MagicDamage` in the future requires zero changes to existing code.

---

**20 — XP scales by defeated enemy's class and level**

`xp_awarded = defeated.xp_reward_base × defeated.level`

*Why it matters:* Makes enemy class identity mechanically meaningful beyond combat stats. A higher-level Sentinel genuinely rewards more than a low-level Executioner. The player's progress feels earned.

---

**21 — `print()` and `logging` are strictly separated**

`print()` is reserved for player-facing narrative output. All internal system events use `logging.INFO` or `logging.WARNING` to a file.

*Why it matters:* Mixing the two creates noise that makes both harder to use. The player shouldn't see log timestamps. The developer's log file shouldn't contain game narrative.

---

**22 — Save/load via JSON with context managers**

`to_dict()` / `from_dict()` on every class. File operations use `with open(...)`. `CorruptSaveError` fires on malformed data.

*Why it matters:* JSON is human-readable, debuggable, and requires no external library. Context managers guarantee the file is closed even if serialization fails mid-write. A specific exception type lets the caller handle save corruption separately from unexpected errors.

---

**23 — Packaging as an installable engine**

`pyproject.toml` makes IronVault installable via `pip install -e .` and exposes an `ironvault` console command.

*Why it matters:* A project that installs like a real package and runs from the terminal feels like a real engine. A project you run with `python main.py` from the right directory does not.

---

## Implementation Decisions

What changed during the build, and why.

---

### `items.py`

| Decision | What Changed | Why |
|----------|-------------|-----|
| `Rarity` stores shorthand + fullname via custom `__init__` | Tuple value `("C", "Common")` unpacked into named attributes | Readable access vs index-based `value[0]` |
| `Gear.STAT_RANGES` replaces separate attack/defense tables | One shared table on `Gear` | Weapon and Armour use identical bounds — the subtraction formula requires balance |
| `max_durability` added to `Weapon` and `Armour` | New attribute alongside `durability` | Required for `RepairKit` to cap repairs correctly |
| Percentage-based `degrade()` | `max(1, int(durability * 0.05))` per use | Achieves rarity-based behavior naturally — higher durability items degrade slower |
| Optional parameters on `__init__` | `attack_power: int \| None = None` pattern | Allows exact stat restoration via `from_dict()` without rerolling |
| `WEIGHT_RANGE` class variable per subclass | Weight generated internally, not passed as parameter | Weight is intrinsic to the item type, not a caller decision |
| `potency` removed from `Potion` | Dropped entirely | No natural "time" mechanic in a CLI turn-based game to tie decay to |
| Consumables not rarity-scaled | Fixed `heal_amount` and `repair_amount` | Simplification — rarity tracking preserved but has no mechanical effect |
| `select_target()` removed from `RepairKit` | Target set by `main.py` directly | Keeps `items.py` free of UI logic |
| `Consumable.use()` changed to abstract | No default `return True` in base class | Forces every subclass to explicitly implement — no ambiguity |

---

### `inventory.py`

| Decision | What Changed | Why |
|----------|-------------|-----|
| `ITEM_NAMES` pyramid pool | 15 Common names → 4 Legendary names per type | Rarity feels distinctive by name pool size, not just stats |
| `to_dict()` and `from_dict()` added | Not in original design | Cleaner encapsulation — `Inventory` owns its own serialization |
| `TypeError` branch in `add_item()` | Defensive — raises if item is neither Gear nor Consumable | Catches bad inputs explicitly rather than silently doing nothing |
| `equip()` delegates to `character.equip_gear()` | Originally called `item.equip(character)` | Slot management belongs on `Character` since `Character` owns the slots |
| `loot_drop()` constructs directly | Uses `Weapon(...)` not `Item.from_dict(...)` | `from_dict()` is for restoring saved state — fresh generation doesn't need it |

---

### `character.py`

| Decision | What Changed | Why |
|----------|-------------|-----|
| `heal()` method added | Not in original design | `Potion.use()` calls `character.heal()` — required to preserve dependency direction |
| `use_consumable()` added | Not in original design | Single clean entry point for all consumable usage |
| `level_up_threshold` made a `@property` | Originally a local variable in `gain_xp()` | `main.py` needs it for XP display without duplicating the formula |
| `equip_gear()` / `unequip_gear()` naming | Originally `equip()` / `unequip()` | More explicit — matches the delegation calls in `inventory.py` |
| `effective_attack` / `effective_defense` return `float` | Originally `int` | Accessory bonus percentage multiplication produces a float |
| XP carries over on level-up | Originally reset to 0 | More realistic — losing overflow XP feels punishing and arbitrary |
| `int()` wrapping on stat increases | `base_health += int(base_health * 0.1)` | Prevents float drift across multiple level-ups |
| Full health restore on level-up | Not in original design | Standard RPG convention — makes level-up feel like a reward |
| `cast()` in `from_dict()` | Not in original design | `Item.from_dict()` returns `Item` — Pylance needs the hint for subclass attributes |

---

### `combat.py`

| Decision | What Changed | Why |
|----------|-------------|-----|
| `calculate_damage` as module-level function | Originally a `@staticmethod` | Has no natural class to belong to — module-level is cleaner |
| Return types changed to `float` | Originally `int` | Consistent with `effective_attack`/`effective_defense` being floats |
| Mid-loop `break` after death | Not in original design | Prevents dead characters from attacking back |
| Broken gear fires once only | Check moved inside `if durability > 0` block | Fires only the turn it breaks, not every subsequent turn |
| Turn count per individual attack | Not specified in original design | Each attack is a discrete event worth counting |

---

### `main.py`

| Decision | What Changed | Why |
|----------|-------------|-----|
| Full interactive game loop | Originally a linear scripted playthrough | Far more engaging — demonstrates the engine's full capability |
| `game_loop()` split from `run()` | Not in original design | Both new game and load game can share the same loop |
| `loot_room()` generic `source_inventory` | Originally always used `character.inventory` | Reusable for dungeon rooms and post-combat enemy drops |
| Load game removed from `game_loop()` | Not in original design | Reassigning `character` inside a function doesn't update the caller's reference |
| `while True` menu in `run()` | Originally recursive `return run()` | Recursion hits Python's call stack limit on repeated invalid inputs |
| Logging to file with UTF-8 | Originally `StreamHandler` to terminal | Windows `cp1252` encoding cannot handle the `→` character in log messages |

---

*For what comes next, see [Future-Extensions.md](Future-Extensions.md).*
