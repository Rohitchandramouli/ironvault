# Future Extensions

> Features that were designed but not built. Each one has a clear implementation path and a documented reason for deferral.

The rule for deferral was simple: if a feature didn't fit within the two-day build window, or if it required more design work than the core system justified at that stage, it was documented here instead of rushed in. Nothing below is an afterthought — most were explicitly designed before being set aside.

---

## Game Mechanics

### Rarity-Scaled Consumables

**What:** Legendary Potions heal significantly more than Common ones. Epic RepairKits restore more durability.

**Why deferred:** Consumables were simplified to fixed-value items during implementation to reduce scope.

**Implementation path:**
- Add `HEAL_RANGES: dict[Rarity, tuple[int, int]]` to `Potion` — same pattern as `Gear.STAT_RANGES`
- Add `REPAIR_RANGES: dict[Rarity, tuple[int, int]]` to `RepairKit`
- Remove `heal_amount` and `repair_amount` as constructor parameters — generate internally from rarity

---

### Potency Decay on Potions

**What:** Potions lose effectiveness the longer they sit unused in inventory. A potion carried through three dungeon rooms heals less than a fresh one.

**Why deferred:** No natural "time" mechanic exists in a CLI turn-based game. "Time" needs a definition — number of rooms cleared, number of turns elapsed, number of combats survived.

**Implementation path:**
- Restore `potency: float` to `Potion.__init__()`, rarity-scaled from 1.0 downward
- `Potion.degrade()` reduces potency by a fixed amount per call (currently a no-op)
- Call `degrade()` on all consumables in `inventory._consumables` each time `loot_room()` is called — rooms cleared becomes the "time" unit
- `Potion.use()` applies `heal_amount × potency` instead of flat `heal_amount`

---

### Agility-Based Turn Order

**What:** Faster characters act first. A Rogue-type with high agility always gets initiative over a slow Sentinel.

**Why deferred:** The four-stat system (Attack, Defense, Magic, Agility) was pulled back to three stats (Attack, Defense, Health) during scope reduction.

**Implementation path:**
- Add `agility` column to `Character.CLASS_STATS_TABLE`
- At the start of `combat()`, compare `char_a.agility` vs `char_b.agility` to determine who goes first
- No changes to the turn loop itself — just swap `char_a` and `char_b` if needed before the loop begins

---

### Per-Class Stat Growth on Level-Up

**What:** Sentinel's health grows faster per level than Executioner's. Executioner's attack grows faster. Each class has a distinct growth curve.

**Why deferred:** Class identity already comes through from starting stats. Divergent growth rates add design complexity without changing the core feel at early levels.

**Implementation path:**
- Add `health_growth`, `attack_growth`, `defense_growth` columns to `CLASS_STATS_TABLE`
- In `Character.gain_xp()`, replace the flat `0.1` multiplier with `self.CLASS_STATS_TABLE[self.char_class.value]["health_growth"]` etc.

---

### Equipment Restrictions Per Class

**What:** Executioners cannot equip heavy armour. Sentinels get a defense bonus when wearing plate. Class identity has mechanical teeth.

**Why deferred:** Adds complexity to `equip_gear()` and requires a restriction table. The flavor exists — it's just not enforced in code.

**Implementation path:**
- Add `allowed_armour_types` and `allowed_weapon_types` to `CLASS_STATS_TABLE`
- Add a check in `Character.equip_gear()` before the isinstance routing
- Raise a new `EquipRestrictionError` on violation

---

## Enemy System

### Enemy Equipment

**What:** Enemies spawn equipped with gear appropriate to their class and level — not fighting with bare base stats.

**Why deferred:** Enemies were simplified to base-stat-only combat during implementation.

**Implementation path:** In `fight_enemy()`:
```python
enemy_weapon = Weapon(name="Enemy Weapon", rarity=random_choice(list(Rarity)))
enemy.inventory.add_item(enemy_weapon)
enemy.equip_gear(enemy_weapon)
# Same for armour
```

---

### Enemy Difficulty Scaling

**What:** Enemy level scales with the player's level. Early fights are easy. Late fights are genuinely dangerous.

**Why deferred:** Enemies always spawn at level 1 — straightforward to change, just wasn't prioritized.

**Implementation path:** In `fight_enemy()`:
```python
enemy_level = max(1, character.level - 1)
enemy = Character(name=..., char_class=enemy_class)
# Then apply level-up iterations to enemy to reach target level
```

---

### Named Enemy Types

**What:** Enemies have names that fit their class — "Iron Sentinel", "Glass Executioner", "Scarred Gladiator".

**Why deferred:** Naming quality matters more than having names at all. Rushed names would be worse than `Enemy GLADIATOR`.

**Implementation path:**
- Add `ENEMY_NAMES: dict[CharacterClass, list[str]]` to `character.py` or `main.py`
- Replace `f"Enemy {enemy_class.value}"` in `fight_enemy()` with `random_choice(ENEMY_NAMES[enemy_class])`

---

## Combat

### Weighted Rarity in `loot_drop()`

**What:** Common items drop far more often than Legendary ones. Currently all five rarities have equal probability.

**Why deferred:** The uniform distribution is technically wrong but not broken for a demo. Weighting matters more when the game has more content.

**Implementation path:**
```python
# Replace:
rarity = choice(list(Rarity))

# With:
rarity = random.choices(
    list(Rarity),
    weights=[50, 30, 12, 6, 2]
)[0]
```

---

### Additional Damage Strategies

**What:** `PoisonDamage`, `MagicDamage`, `ArmorPiercingDamage` — damage types that interact with stats differently.

**Why deferred:** The strategy pattern exists precisely so these can be added without touching the turn loop. They were deferred, not forgotten.

**Implementation path:** For each new type, inherit from `DamageStrategy` and implement `apply()`. Zero changes to `combat()`.

---

### Critical Hit Probability

**What:** A random 15% chance per attack to deal critical damage during normal combat — not just when explicitly using `CriticalDamage` strategy.

**Implementation path:** In `combat()`'s turn loop:
```python
if random.random() < 0.15:
    damage = CriticalDamage().apply(attacker, defender)
else:
    damage = strategy.apply(attacker, defender)
```

---

## Architecture

### Observer Pattern for Combat Events

**What:** Instead of printing directly from `combat.py`, fire events that UI, logger, and future systems can listen to independently.

**Why deferred:** Meaningful but complex — requires an event dispatcher and listener registration. The current direct-print approach works for a CLI.

**Proposed design:**
```python
class WeaponBrokeEvent:
    character: Character
    weapon: Weapon

class LevelUpEvent:
    character: Character
    new_level: int

# combat() fires events, never prints directly
# main.py subscribes and handles display
```

---

### Richer Stat System

**What:** Four stats (Attack, Defense, Magic, Agility) plus three resource bars (HP, MP, Stamina). Mages use MP for spells. Rogues consume Stamina for abilities.

**Why deferred:** Explicitly pulled back during the design phase. The current three-stat system was the right scope for the initial build.

**Implementation path:** Requires new columns in `CLASS_STATS_TABLE`, new `effective_*` properties on `Character`, new consumable types (`ManaPotion`, `StaminaPotion`), and changes to the combat formula to use Magic stat.

---

### CLI Flags

**What:** `ironvault --help`, `ironvault --version`, `ironvault new`, `ironvault load <file>`

**Why deferred:** The game works as a single `ironvault` command. Subcommands add polish but not capability.

**Implementation path:** Add `argparse` to `main.py`'s `run()` function. Route subcommands to the appropriate function.

---

### Multiple Save Slots

**What:** Named save slots with a browser and overwrite confirmation, instead of typing a filename every time.

**Implementation path:** A `saves/` directory with numbered or named slot files. A slot browser in `run()` before calling `load_game()`.

---

## Testing

### Additional Edge Cases

These were deprioritized in favor of getting core coverage to 30 tests:

| Test | What it covers |
|------|---------------|
| `RepairKit` with `selected_target = None` | `use()` should no-op cleanly, not crash |
| `Accessory` full `to_dict()` / `from_dict()` round-trip | Verifies `bonus_percentage` is restored exactly |
| Multiple level-ups from one `gain_xp()` call | The `while True` loop handles chained level-ups |
| `loot_drop()` with inventory already at max weight | Generator stops cleanly, no partial adds |
| `Character` save/load with all three equipment slots occupied | Full state restoration under load |
| `CriticalDamage` always produces ≥ `NormalDamage` | Edge case where `calculate_damage` returns 0 |

---

*For the reasoning behind what was built, see [Engineering-Decisions.md](Engineering-Decisions.md).*
