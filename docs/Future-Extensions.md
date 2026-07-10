# Future Extensions

These features were explicitly designed during IronVault's architecture phase but deferred from the initial implementation. Each one has a documented reason for deferral and a clear path to implementation.

---

## Game Mechanics

**Rarity-scaled consumables**
Potions and RepairKits currently have fixed values (`heal_amount=50`, `repair_amount=30`). The design anticipated rarity scaling — a Legendary Potion healing significantly more than a Common one — but was deferred when consumables were simplified to fixed-value items during implementation. Adding this requires a `HEAL_RANGES` class variable on `Potion` and a `REPAIR_RANGES` class variable on `RepairKit`, following the same pattern as `Gear.STAT_RANGES`.

**Potency decay on Potions**
`Potion.degrade()` exists as an abstract implementation but is currently a no-op. The original design intended potency to decay over dungeon progression — one `degrade()` call per room cleared. Deferred because "time" in a CLI turn-based game has no natural clock. Implementation path: call `degrade()` on all consumables in `inventory._consumables` each time `loot_room()` is called.

**Agility-based turn order**
Combat currently gives `char_a` initiative always — player always goes first. Speed or agility stat determining who acts first was designed but deferred when the four `CharacterClass` stats were simplified. Implementation path: add `agility` to `CLASS_STATS_TABLE` and sort by it at the start of `combat()`.

**Per-class stat growth rates on level-up**
Level-up currently applies a flat 10% to all three stats regardless of class. Sentinel growing defense faster than Executioner was considered and explicitly deferred. Implementation path: add `health_growth`, `attack_growth`, `defense_growth` columns to `CLASS_STATS_TABLE` and use them in `gain_xp()` instead of the flat 0.1.

**Dual weapon slots**
Single weapon slot enforced. Architecture supports multiple slots with minimal changes to `Character.__init__()`, `equip_gear()`, `unequip_gear()`, `effective_attack`, `to_dict()`, and `from_dict()`.

**Equipment restrictions per class**
A Sentinel can technically equip zero armour. Class-based equipment restrictions — Executioner cannot equip armour, Sentinel gets a bonus when using heavy plate — were explicitly deferred as flavor-only for the initial build.

---

## Enemy System

**Enemy equipped with starter gear**
Enemies currently spawn with no equipment — they fight with base stats only. Implementation path: in `fight_enemy()`, construct a `Weapon` and `Armour` at an appropriate rarity for the enemy's level, add to inventory, and call `equip_gear()` before `combat()`.

**Enemy difficulty scaling**
Enemies always spawn at level 1. Implementation path: scale enemy level to `max(1, character.level - 1)` so fights get harder as the player progresses.

**Named enemy types**
Current enemies are named `"Enemy GLADIATOR"` etc. A name pool per `CharacterClass` — "Iron Sentinel", "Glass Executioner" — would make encounters feel more distinct.

---

## Combat

**Weighted rarity probability in `loot_drop()`**
Currently selects rarity uniformly via `choice(list(Rarity))`. A real RPG would weight Common drops far more heavily than Legendary ones. Implementation path: replace `choice(list(Rarity))` with `random.choices(list(Rarity), weights=[50, 30, 12, 6, 2])`.

**Additional damage strategies**
`PoisonDamage`, `MagicDamage`, `ArmorPiercingDamage` — natural extensions of the strategy pattern. Adding any of these requires only a new class inheriting from `DamageStrategy`. `combat()`'s turn loop never changes.

**Critical hit probability**
`CriticalDamage` exists but is never randomly triggered during normal combat — it must be passed explicitly as the strategy. A random critical hit chance per turn (e.g., 15%) would make `CriticalDamage` meaningful in practice.

---

## Items

**Shop mechanic for gear repair**
The design mentioned a shop NPC where broken gear could be repaired. Currently repair is `RepairKit`-only. A shop system would require a currency mechanic (gold drops from enemies) and a shop interface in `main.py`. The repair logic itself already exists in `RepairKit.use()`.

**Observer pattern for combat events**
The design proposed `WeaponBrokenEvent`, `LevelUpEvent` etc. so UI, logger, and future systems could listen independently. Currently combat events fire directly to `print()` and `logger`. An event system would make IronVault extensible as a library — callers could subscribe to events without modifying the engine.

---

## Architecture

**Richer stat system**
The design considered four stats (Attack, Defense, Magic, Agility) plus three resource bars (HP, MP, Stamina). These were explicitly pulled back to three stats and one resource bar (HP) for scope. Adding Magic and Agility would require new columns in `CLASS_STATS_TABLE`, new `effective_*` properties on `Character`, and new consumable types (Mana Potion, Stamina Potion).

**ECS migration**
Entity Component System as the next architectural layer. Characters, enemies, items, and combat effects become entities with attached components rather than class hierarchies. A natural evolution once the current architecture is thoroughly understood.

**`python -m ironvault` and CLI flags**
The `ironvault` console command works but has no `--help`, no `--version`, no subcommands. Adding `argparse` to `main.py` and supporting `ironvault new`, `ironvault load <file>`, `ironvault --version` would make it feel like a real CLI tool.

**Multiple save slots**
Currently one save file per filename typed. Named save slots with a slot browser and overwrite confirmation would make the save system more robust.

---

## Testing

**Additional edge case tests**
30 tests cover the core contracts. These were deferred as lower priority than getting core coverage:

- `RepairKit` with `selected_target = None` — `use()` should no-op cleanly
- `Accessory` round-trip via `to_dict()` / `from_dict()`
- Multiple level-ups from a single `gain_xp()` call
- `loot_drop()` with an inventory already at max weight
- `Character` with all three equipment slots occupied, then saving and loading
