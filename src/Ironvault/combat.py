"""
This module contains the combat system for the Ironvault game.
It defines the combat mechanics, including attack, defense, and damage calculations.
It contains the `combat`, `calculate_damage` functions, and the `DamageStrategy` class for different damage calculation strategies as subclasses
It depends on the `character` module for character definitions.
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

from Ironvault.character import Character

logger = logging.getLogger(__name__)

class DamageStrategy(ABC):
    """Abstract base class for damage calculation strategies."""
    @abstractmethod
    def apply(self, attacker: Character, defender: Character) -> float:
        """Calculate the damage dealt by the attacker to the defender."""
        pass

class NormalDamage(DamageStrategy):
    """Normal damage calculation strategy."""
    def apply(self, attacker: Character, defender: Character) -> float:
        return calculate_damage(attacker.effective_attack, defender.effective_defense)

class CriticalDamage(DamageStrategy):
    """Critical damage calculation strategy."""
    def apply(self, attacker: Character, defender: Character) -> float:
        damage = calculate_damage(attacker.effective_attack, defender.effective_defense)
        return damage * 1.5

@dataclass
class CombatResult:
    winner: Character
    defeated: Character
    turn_count: int
    final_health: dict[str, int]


def calculate_damage(attack: float, defense: float) -> float:
    """Calculate the damage dealt by the attacker to the defender."""
    base_damage = attack - defense
    if base_damage < 0:
        base_damage = 0
    return base_damage

def combat(char_a: Character, char_b: Character, strategy: DamageStrategy = NormalDamage()) -> CombatResult:
    """Simulate combat between two characters using the specified damage strategy."""
    turn_count = 0
    while char_a.health > 0 and char_b.health > 0:
        damage_a_to_b = strategy.apply(char_a, char_b)
        char_b.health = int(max(0, char_b.health - damage_a_to_b))
        turn_count += 1

        # After attacker hits:
        if char_a.equipped_weapon and char_a.equipped_weapon.durability > 0:
            char_a.equipped_weapon.degrade()
            if char_a.equipped_weapon.durability == 0:
                print(f"{char_a.name} fights bare-fisted!")
                logger.warning("%s's weapon broke mid-combat.", char_a.name)
        if char_a.equipped_armour and char_a.equipped_armour.durability > 0:
            char_a.equipped_armour.degrade()
            if char_a.equipped_armour.durability == 0:
                print(f"{char_a.name} is unarmored!")
                logger.warning("%s's armour broke mid-combat.", char_a.name)

        logger.info("%s attacks %s for %d damage. %s has %d health left.", char_a.name, char_b.name, damage_a_to_b, char_b.name, char_b.health)
        print(f"{char_a.name} attacks {char_b.name} for {int(damage_a_to_b)} damage. {char_b.name} has {char_b.health} HP left.")

        if char_b.health == 0:
            break  # char_b is dead, don't let them attack back

        damage_b_to_a = strategy.apply(char_b, char_a)
        char_a.health = int(max(0, char_a.health - damage_b_to_a))
        turn_count += 1

        if char_b.equipped_weapon and char_b.equipped_weapon.durability > 0:
            char_b.equipped_weapon.degrade()
            if char_b.equipped_weapon.durability == 0:
                print(f"{char_b.name} fights bare-fisted!")
                logger.warning("%s's weapon broke mid-combat.", char_b.name)
        if char_b.equipped_armour and char_b.equipped_armour.durability > 0:
            char_b.equipped_armour.degrade()
            if char_b.equipped_armour.durability == 0:
                print(f"{char_b.name} is unarmored!")
                logger.warning("%s's armour broke mid-combat.", char_b.name)

        logger.info("%s attacks %s for %d damage. %s has %d health left.", char_b.name, char_a.name, damage_b_to_a, char_a.name, char_a.health)
        print(f"{char_b.name} attacks {char_a.name} for {int(damage_b_to_a)} damage. {char_a.name} has {char_a.health} HP left.")

    winner = char_a if char_b.health == 0 else char_b
    defeated = char_b if char_b.health == 0 else char_a

    logger.info("Combat ended. %s has %d health left. %s has %d health left.Combat ended in %d turns. Winner: %s, Defeated: %s", char_a.name, char_a.health, char_b.name, char_b.health, turn_count, winner.name, defeated.name)
    print(f"\nCombat ended! {winner.name} wins after {turn_count} turns.")

    return CombatResult(
        winner=winner,
        defeated=defeated,
        turn_count=turn_count,
        final_health={char_a.name: int(char_a.health), char_b.name: int(char_b.health)}
    )