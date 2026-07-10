# Engineering Decisions

Every architectural decision in IronVault was made before implementation began. This document records what was decided, why, and what changed during implementation. It is organized by file in dependency order.

---

## Original Design Decisions — Made Before Implementation

These 27 decisions were locked in during the design phase. None were changed without explicit reasoning documented in the implementation section below.

**1. Dependency direction is strictly one-way**
`items.py → inventory.py → character.py → combat.py → main.py`. No file imports from anything above it in the chain. Prevents circular imports, keeps each module independently testable, makes responsibility unambiguous.

**2. Composition over inheritance for `Character`**
`Character` *has* an `Inventory`, it does not extend one. Inheritance would couple every `Character` method to every `Inventory` method — a fragile coupling that makes the class harder to reason about and extend.

**3. Abstract base classes over duck typing**
`Item`, `Gear`, `Consumable`, and `DamageStrategy` are all abstract. Contracts need to be enforced at class definition time, not discovered at runtime when a missing method causes an unexpected `AttributeError` mid-combat.

**4. `Item` is lean by design**
`Item` only defines what is genuinely true of every single item: `name`, `rarity`, `weight`, and the three abstract method contracts. A generic shared `condition` field that subclasses reinterpret was explicitly rejected as crowding the base class with irrelevant state.

**5. `Gear` exists purely for equip/unequip behavior**
`Gear` does not hold `durability` — that lives on `Weapon` and `Armour` individually because `Accessory` has no durability concept. `Gear`'s only job is to represent "this item is equippable."

**6. Durability range is shared between `Weapon` and `Armour`**
Both scale off the same rarity-based durability table since the lifecycle concept is identical. This also keeps attack and defense balanced for the subtraction damage formula.

**7. Rarity scales stats, not weight**
Weight is a physical property of what an item is, not how powerful it is. A Legendary potion is not heavier than a Common one. Weight ranges are defined locally per subclass.

**8. Centralize when shared, keep local when independent**
The rarity scaling tables are centralized because multiple subclasses read the same values. Weight ranges are kept local because each subclass has independent values with no shared logic.

**9. `degrade()` is abstract on `Item` even for `Accessory`**
`Accessory`'s `degrade()` is a deliberate no-op. Making it abstract signals that every item in this world has a lifecycle, even if some choose not to act on it.

**10. `use()` contract is uniform, with one justified exception**
Every item's `use()` takes `character` as its only parameter. `RepairKit` is the single exception — it adds `select_target()` as a separate method called before `use()`, rather than breaking the uniform signature. This keeps the polymorphic contract intact while preserving player agency.

**11. `Consumable` signals its own removal via return value**
`Consumable.use()` returns `True` to signal "remove me from inventory." The alternative — holding a back-reference to the `Inventory` — would create a dependency from `items.py` upward to `inventory.py`, violating the one-way chain.

**12. `loot_drop()` has no side effects**
The generator yields items and does nothing else. The caller decides what to do with each one, including whether to handle `InventoryFullError` mid-loop. Keeps "generating loot" and "managing capacity" as separate concerns.

**13. Inventory stores gear and consumables in separate private lists**
Type-based routing at `add_item()` time. The lists are private; `gear` and `consumables` are properties returning copies, protecting internal state from external mutation.

**14. Equipped items stay in inventory**
When gear is equipped, it stays in `_gear` with `is_equipped = True`. One source of truth for everything a character possesses. Two lists tracking the same items would be a synchronization bug waiting to happen.

**15. Single equipment slot per gear type**
One weapon, one armour, one accessory. Equipping a new item unequips the previous occupant. Dual-wielding explicitly deferred.

**16. Broken gear silently degrades stats, not crashes combat**
When durability hits zero, `effective_attack` and `effective_defense` silently exclude the broken item's bonus via a durability check inside the property. The item stays equipped but contributes nothing. `BrokenItemError` only fires if `use()` is called directly on a broken item.

**17. Bare-fisted and unarmoured are explicit states**
A character with no weapon, or a broken weapon, is explicitly labeled "bare-fisted" in combat output. Same for armour. Player-facing clarity, not just a fallback.

**18. Accessory bonus applies to base stat only**
Applying the bonus to the already-equipment-modified effective stat would make equip order matter. Applying to `base_attack` / `base_defense` only makes the calculation order-independent.

**19. `CharacterClass` sets starting stats only**
Class identity determines starting values. It does not restrict equipment choices or change how stats are calculated. Equipment restrictions are flavor only.

**20. `Character` serves as both player and enemy**
There is no separate `Enemy` class. Both are `Character` instances. `combat()` operates only against the `Character` interface. Avoids duplicating logic.

**21. XP scales by defeated enemy's class and level**
`xp_awarded = defeated.xp_reward_base * defeated.level`. Makes enemy class identity mechanically meaningful beyond combat stats.

**22. Level-up applies flat percentage stat increase**
All three stats grow by 10% on level-up regardless of class. Per-class growth rates were considered and explicitly deferred.

**23. `Item.from_dict()` as centralized construction**
All item construction flows through this single classmethod factory. Prevents construction logic from being scattered across `loot_drop()`, `load_game()`, and any future spawning system.

**24. Strategy pattern for damage calculation**
`DamageStrategy` with `NormalDamage` and `CriticalDamage` means `combat()`'s turn loop never changes when new damage types are added. Open for extension, closed for modification.

**25. Logging over print for internal system events**
`print()` is reserved for player-facing narrative output. All internal system events use `logging.INFO` or `logging.WARNING`. Two separate concerns, never mixed.

**26. Save/load via JSON with context managers**
Game state serializes to JSON via `to_dict()` / `from_dict()` round-tripping. File operations use context managers. `CorruptSaveError` fires on malformed or missing fields.

**27. Packaging as an installable engine**
`pyproject.toml` makes IronVault installable via `pip install -e .` and exposes an `ironvault` console command. Presents the project as a small framework, not a script.

---

## Implementation Decisions — `items.py`

### Added During Implementation

**1. `Rarity` stores shorthand and fullname via custom `__init__`**
Tuple value `("C", "Common")` unpacked into `.shorthand` and `.fullname` attributes. Readable access rather than index-based `value[0]` and `value[1]`.

**2. `BonusType` stores full name as string value**
String value serves as the outer key into `Accessory.BONUS_RANGES` and is serialized directly in `to_dict()`. Reconstruction uses `BonusType(data["bonus_type"])` — lookup by value, not by name.

**3. `Gear.STAT_RANGES` replaces separate `Weapon.ATTACK_RANGES` and `Armour.DEFENSE_RANGES`**
Merged into one shared table on `Gear` since Weapon and Armour use identical numerical bounds, justified by the subtraction damage formula requiring balanced ranges.

**4. `max_durability` added to `Weapon` and `Armour`**
Required for the `RepairKit` cap mechanic. `max_durability` is rolled once at creation and never changes. `durability` starts equal to `max_durability` and degrades with use.

**5. Percentage-based `degrade()` — `max(1, int(durability * 0.05))`**
5% of current durability per use, floored at 1. Achieves rarity-based behavior naturally — higher durability items degrade slower in absolute terms — without a separate per-rarity degradation table.

**6. Optional parameters on `Weapon` and `Armour` `__init__`**
`attack_power`, `max_durability`, `durability` all `int | None = None`. When `None`, stats are randomly generated from rarity tables. When provided (via `from_dict()`), saved values are restored exactly. Uses `is not None` check rather than `or` to avoid treating legitimate `0` values as falsy.

**7. Optional `weight` and `bonus_percentage` on subclass `__init__`**
Same pattern — generate randomly at creation, but preserve exact values through save/load.

**8. `WEIGHT_RANGE` class variable on every concrete subclass**
Originally a free parameter passed by the caller. Changed to intrinsic property generated internally per subclass from a fixed range.

**9. `logger.warning()` before `BrokenItemError`**
Fires immediately before the exception is raised so the log record exists even if the exception is caught upstream.

**10. `from_dict()` placed on `Item` before subclasses in file**
Works correctly because `from_dict()` body only executes at call time — by then all subclasses exist in the module namespace. The apparent forward-reference is intentional.

**11. `heal()` method implicitly required on `Character`**
`Potion.use()` calls `character.heal(self.heal_amount)`. `Character` must implement `heal()` — not in the original design spec, added as a required method to preserve the dependency direction.

### Changed During Implementation

**12. `Consumable.use()` changed from concrete to abstract**
Originally a concrete method returning `True`. Changed to `@abstractmethod` — forcing every subclass to explicitly implement it.

**13. `select_target()` removed from `RepairKit`**
Target selection responsibility moved to `main.py`, which sets `repair_kit.selected_target` directly. Keeps `items.py` free of any UI logic.

### Removed During Implementation

**14. `potency` removed from `Potion`**
Dropped because consumables were redesigned as fixed-value items and "time" in a CLI turn-based game has no natural clock to tie decay to.

**15. Consumables are not rarity-scaled**
`heal_amount` and `repair_amount` are fixed parameters at creation. Rarity is still tracked but has no mechanical effect on consumable stats.

---

## Implementation Decisions — `inventory.py`

### Added During Implementation

**1. `ITEM_NAMES` constant with pyramid pool structure**
Module-level constant mapping each concrete item class to a name pool per rarity tier. Pyramid structure — 15 Common weapon names, 4 Legendary weapon names — so Legendary items feel rarer by name distinctiveness, not just stats.

**2. `to_dict()` and `from_dict()` added to `Inventory`**
Not in original design. `Character.to_dict()` was meant to handle inventory serialization directly. Added for cleaner encapsulation — `Inventory` owns its own serialization.

**3. `TypeError` branch in `add_item()` and `remove_item()`**
Defensive programming — if something that is neither `Gear` nor `Consumable` is passed in, raises `TypeError` with `logger.error()`.

**4. Membership check in `equip()` and `unequip()`**
Before delegating to `character.equip_gear()`, verifies the item actually exists in `_gear`. Prevents equipping items that were never added to inventory.

### Changed During Implementation

**5. `loot_drop()` constructs directly, not via `Item.from_dict()`**
Direct concrete subclass construction is cleaner for fresh random generation. `Item.from_dict()` is designed for reconstruction from saved data with all fields provided.

**6. `equip()`/`unequip()` delegate to `character.equip_gear()`/`character.unequip_gear()`**
Originally intended to call `item.equip(character)`. Changed to call character methods instead — slot management responsibility belongs on `Character` since `Character` owns the slot state.

---

## Implementation Decisions — `character.py`

### Added During Implementation

**1. `heal()` method**
Required by `Potion.use()`. Capped at `base_health`. No logging inside `heal()` — output handled by `use_consumable()`.

**2. `use_consumable()` method**
Single clean entry point for all consumable usage. Checks membership, calls `item.use(self)`, removes from inventory, logs per type.

**3. `xp_reward_base` as instance attribute**
Stored on `self` for direct access by `combat.py`. Serialized in `to_dict()` and restored in `from_dict()`.

**4. Before/after stat change display on equip**
Snapshot before slot assignment, then both `print()` for player-facing output and `logger.info()` for engine diagnostics after equipping.

**5. Full health restore on level-up**
Standard RPG convention. Makes level-up feel like a meaningful reward moment.

**6. `cast()` for equipped item reconstruction in `from_dict()`**
`Item.from_dict()` returns `Item` — Pylance cannot verify the specific subclass. `cast()` resolves static analysis warnings without changing runtime behavior.

**7. `level_up_threshold` added as `@property`**
Originally calculated inline in `gain_xp()`. Made a property so `main.py` can display XP progress without duplicating the formula.

### Changed During Implementation

**8. `char_class` instead of `character_class`**
Shortened for readability. Consistent throughout the file.

**9. `equip()` renamed to `equip_gear()`, `unequip()` to `unequip_gear()`**
More explicit. Matches the method names referenced in `inventory.py`'s delegation calls.

**10. `effective_attack` and `effective_defense` return `float` not `int`**
Accessory `bonus_percentage` multiplication produces a float. Display uses `:.0f` formatting so players never see decimal places.

**11. XP carries over on level-up**
Originally designed to reset to 0. Changed to `current_xp -= level_up_threshold` so excess XP carries into the next level. More realistic.

**12. `int()` wrapping on stat increases**
`base_health * 1.1` produces a float. `int()` wrapping maintains integer stats and prevents type drift across multiple level-ups.

---

## Implementation Decisions — `combat.py`

### Added During Implementation

**1. `CombatResult` as a dataclass**
`@dataclass` auto-generates `__init__`, `__repr__`, and `__eq__`. Clean, minimal, modern Python.

**2. Mid-loop `break` after `char_b` health hits 0**
Prevents a dead character from attacking back. Not specified in original design.

**3. Broken gear notification fires only the turn durability hits zero**
Moved check inside the `if durability > 0` block — fires only when `degrade()` causes durability to reach exactly 0 that turn, not on every subsequent turn. Prevents repeated spam.

### Changed During Implementation

**4. `calculate_damage` as module-level function, not staticmethod**
Has no natural class to belong to in `combat.py`. Module-level function is cleaner and functionally identical.

**5. Return types changed to `float`**
Consistent with `effective_attack`/`effective_defense` being floats. Health cast back to `int` at application point.

**6. Turn count increments per individual attack**
Each attack is a discrete event. A fight where both characters attack 5 times each reports `turn_count = 10`.

---

## Implementation Decisions — `main.py`

### Added During Implementation

**1. Full interactive game loop instead of scripted playthrough**
Original design described a linear demo script. Replaced with a repeating `game_loop()` with player-driven options.

**2. Five helper functions**
`show_character_status()`, `loot_room()`, `equip_menu()`, `consumable_menu()`, `fight_enemy()` — keeps `game_loop()` readable.

**3. `game_loop()` split from `run()`**
`run()` handles opening menu only. `game_loop()` handles repeating options. Both new game and load game share the same loop.

**4. `loot_room()` generic `source_inventory` parameter**
Reusable for both dungeon room looting and post-combat enemy loot drops without duplicating code. Optional `header` parameter for narrative context.

**5. `fight_enemy()` returns `bool`**
Signals victory/defeat to `game_loop()` so the loop can break cleanly on game over.

**6. `while True` opening menu in `run()` with `continue`/`break`**
Replaced recursive `return run()` calls — recursion would hit Python's call stack limit on repeated invalid inputs.

### Changed During Implementation

**7. Starter weapon constructed directly, not via `Item.from_dict()`**
`Weapon(name=..., rarity=Rarity.COMMON)` directly — simpler and more readable for a hardcoded starter item.

**8. Load game removed from `game_loop()` options**
Reassigning `character` inside `game_loop()` doesn't update the caller's reference in Python. Load game available from opening menu in `run()` only.

---

## Implementation Decisions — Tests, Packaging, CI

**1. `conftest.py` with shared fixtures**
Centralizes test object creation. Fixtures use fixed deterministic values (`attack_power=20`, `max_durability=50`) so tests are reproducible regardless of random seed.

**2. `MagicMock` for item tests**
Keeps item tests isolated from character implementation. Tests item behavior without depending on `Character`'s internal health management.

**3. `pytest.approx()` for float comparisons**
`effective_attack`/`effective_defense` return `float`. Direct `==` comparison fails due to floating point precision.

**4. `cast()` in tests**
`Item.from_dict()` returns `Item` — subclass-specific attributes need `cast()` to satisfy Pylance without changing runtime behavior.

**5. `tmp_path` for save/load tests**
Built-in pytest fixture. Eliminates hardcoded file paths and manual cleanup.

**6. Tests 1-2 moved from `test_items.py` to `test_inventory.py`**
`add_item()` routing tests belong in `test_inventory.py` since they test `Inventory` behavior, not `Item` behavior.

**7. Test 6 replaced**
"Potion.degrade() reduces potency" → "Potion.use() calls character.heal() with correct heal_amount" — reflects potency being dropped during implementation.

**8. Package name `Ironvault` not `ironvault`**
Follows actual folder naming used throughout implementation.

**9. `[tool.pytest.ini_options]` added to `pyproject.toml`**
`testpaths` and `pythonpath` ensure pytest finds tests and resolves imports correctly in all environments.

**10. Logging to file with UTF-8 encoding**
Windows PowerShell's default `cp1252` encoding cannot encode the `→` arrow character used in equip stat-change logs. File logging with `encoding="utf-8"` resolves the `UnicodeEncodeError`.
