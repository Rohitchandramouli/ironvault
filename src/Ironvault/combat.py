"""
This module contains the combat system for the Ironvault game.
It defines the combat mechanics, including attack, defense, and damage calculations.
It contains the `combat`, `calculate_damage`, and `StrategyPattern` classes, which handle the combat between two characters and different combat strategies as subclasses.
It depends on the `character` module for character definitions.
"""

from abc import ABC, abstractmethod
import logging

from Ironvault.character import Character, CharacterClass

logger = logging.getLogger(__name__)

@abstractmethod
class Damage_Strategy(ABC):
    """Abstract base class for damage calculation strategies."""

    @abstractmethod
    def apply(self, attacker: Character, defender: Character) -> int:
        """Calculate the damage dealt by the attacker to the defender."""
        pass

class NormalDamage(Damage_Strategy):
    """Normal damage calculation strategy."""

    def apply(self, attacker: Character, defender: Character) -> int:
        return calculate_damage(attacker.effective_attack, defender.effective_defense)

class CriticalDamage(Damage_Strategy):
    """Critical damage calculation strategy."""

    def apply(self, attacker: Character, defender: Character) -> int:
        damage = calculate_damage(attacker.effective_attack, defender.effective_defense)
        return int(damage * 1.5)

@staticmethod
def calculate_damage(attack: int, defense: int) -> int:
    """Calculate the damage dealt by the attacker to the defender."""
    base_damage = attack - defense
    if base_damage < 0:
        base_damage = 0
    return base_damage

def combat(char_a: Character, char_b: Character, strategy: Damage_Strategy = NormalDamage()) -> Combat_Result:
    """Simulate combat between two characters using the specified damage strategy."""
    while char_a.health > 0 and char_b.health > 0:
        damage_a_to_b = strategy.apply(char_a, char_b)
        char_b.health -= damage_a_to_b

        if char_a.equipped_weapon.durability <= 0:
            char_a.equipped_weapon.durability -= 1
        else:
            char_a.effective_attack -= char_a.equipped_weapon.base_attack
            logger.warning("%s's weapon is broken! Effective attack reduced to %d.", char_a.name, char_a.effective_attack)
            print(f"{char_a.name}'s weapon is broken! Effective attack reduced to {char_a.effective_attack}.{char_a.name} is barefisted and vulnerable to attacks.")

        if char_a.equipped_armour.durability <= 0:
            char_a.equipped_armour.durability -= 1
        else:
            char_a.effective_defense -= char_a.equipped_armour.base_defense
            logger.warning("%s's armour is broken! Effective defense reduced to %d.", char_a.name, char_a.effective_defense)
            print(f"{char_a.name}'s armour is broken! Effective defense reduced to {char_a.effective_defense}.{char_a.name} is unarmored and vulnerable to attacks.")

        logger.info("%s attacks %s for %d damage. %s has %d health left.", char_a.name, char_b.name, damage_a_to_b, char_b.name, char_b.health)

        damage_b_to_a = strategy.apply(char_b, char_a)
        char_a.health -= damage_b_to_a
        if char_b.equipped_weapon.durability <= 0:
            char_b.equipped_weapon.durability -= 1
        else:
            char_b.effective_attack -= char_b.equipped_weapon.base_attack
            logger.warning("%s's weapon is broken! Effective attack reduced to %d.", char_b.name, char_b.effective_attack)
            print(f"{char_b.name}'s weapon is broken! Effective attack reduced to {char_b.effective_attack}.{char_b.name} is barefisted and vulnerable to attacks.")
        if char_b.equipped_armour.durability <= 0:
            char_b.equipped_armour.durability -= 1
        else:
            char_b.effective_defense -= char_b.equipped_armour.base_defense
            logger.warning("%s's armour is broken! Effective defense reduced to %d.", char_b.name, char_b.effective_defense)
            print(f"{char_b.name}'s armour is broken! Effective defense reduced to {char_b.effective_defense}.{char_b.name} is unarmored and vulnerable to attacks.")

        logger.info("%s attacks %s for %d damage. %s has %d health left.", char_b.name, char_a.name, damage_b_to_a, char_a.name, char_a.health)

    logger.info("Combat ended. %s has %d health left. %s has %d health left.", char_a.name, char_a.health, char_b.name, char_b.health)
    return Combat_Result