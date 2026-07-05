"""
Entry point and orchestration layer for the IronVault engine.
Contains save_game(), load_game(), and the run() function exposed as the `ironvault` console command via pyproject.toml.
Also defines CorruptSaveError for malformed save file handling.
Has no game logic of its own — coordinates Character, Inventory, Item, and combat systems to produce a complete playthrough.
"""

import logging
import json
from random import choice as random_choice

from Ironvault.items import Rarity, Item, Weapon, Armour, Accessory, Potion, RepairKit
from Ironvault.inventory import Inventory, InventoryFullError
from Ironvault.character import Character, CharacterClass
from Ironvault.combat import combat, CombatResult, NormalDamage


logger = logging.getLogger(__name__)

class CorruptSaveError(RuntimeError):
    """Raised when a save file is found to be malformed or corrupted."""
    pass

def save_game(character: Character, filename: str) -> None:
    """Save the character's state to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(character.to_dict(), f, indent=2)
        logger.info("Game saved successfully to %s.", filename)
    except Exception as e:
        logger.error("Failed to save game: %s", e)
        raise

def load_game(filename: str) -> Character:
    """Load the character's state from a JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            return Character.from_dict(data)
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to load game: %s", e)
        raise CorruptSaveError("The save file is corrupted or malformed.") from e
    except FileNotFoundError:
        logger.error("Save file not found: %s", filename)
        raise CorruptSaveError(f"Save file not found: {filename}")
    except Exception as e:
        logger.error("Failed to load game: %s", e)
        raise

def show_character_status(character: Character) -> None:
    """Display the character's current status."""
    print(f"\nCharacter Status:")
    print(f"Name: {character.name}")
    print(f"Class: {character.char_class.value}")
    print(f"Level: {character.level}")
    print(f"XP: {character.current_xp}/{character.level_up_threshold}")
    print(f"Health: {character.health}/{character.base_health}")
    print(f"Attack: {character.effective_attack}")
    print(f"Defense: {character.effective_defense}")
    print(f"Equipped Weapon: {character.equipped_weapon.name if character.equipped_weapon else 'None'}")
    print(f"Equipped Armor: {character.equipped_armour.name if character.equipped_armour else 'None'}")
    print(f"Equipped Accessory: {character.equipped_accessory.name if character.equipped_accessory else 'None'}")
    print(f"Inventory Count: {len(character.inventory)}")
    print(f"Inventory: {character.inventory}")

def loot_room(character: Character, source_inventory: Inventory, header: str = "You enter a Dungeon Room...") -> None:
    """Simulate looting a room with random items."""
    print(f"\n{header}")
    for item in source_inventory.loot_drop():
        try:
            print(f"\nYou found: {item.name} ({item.rarity.fullname})")
            if isinstance(item, Weapon):
                print(f"  Attack Power: {item.attack_power} | Durability: {item.durability}/{item.max_durability}")
            elif isinstance(item, Armour):
                print(f"  Defense Rating: {item.defense_rating} | Durability: {item.durability}/{item.max_durability}")
            elif isinstance(item, Accessory):
                print(f"  Bonus: {item.bonus_type.value} +{item.bonus_percentage:.1%}")
            elif isinstance(item, Potion):
                print(f"  Heals: {item.heal_amount} HP")
            elif isinstance(item, RepairKit):
                print(f"  Repairs: {item.repair_amount} durability")
            choice = input("Pick it up? (y/n): ").strip().lower()
            if choice == 'y':
                character.inventory.add_item(item)
                print(f"{item.name} added to inventory.")
        except InventoryFullError:
            print(f"Your inventory is full! You cannot pick up: {item.name}")
            logger.warning("%s's inventory is full. Could not loot item: %s", character.name, item)
            break

def equip_menu(character: Character) -> None:
    """Allow the player to equip items from their inventory."""
    gear = character.inventory.gear
    if not gear:
        print("\nNo gear available to equip.")
        return
    print("\nEquip Menu:")
    for idx, item in enumerate(gear):
        print(f"{idx + 1}. {item.name} ({item.rarity.fullname})")
    while True:
        choice = input("Select an item number to equip (or 'q' to quit): ").strip().lower()
        if choice == 'q':
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(gear):
                character.equip_gear(gear[idx])
                break
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a number or 'q'.")

def consumable_menu(character: Character) -> None:
    """Allow the player to use consumable items from their inventory."""
    consumables = character.inventory.consumables
    if not consumables:
        print("\nNo consumables available to use.")
        return
    print("\nConsumable Menu:")
    for idx, item in enumerate(consumables):
        print(f"{idx + 1}. {item.name} ({item.rarity.fullname})")
    while True:
        choice = input("Select an item number to use (or 'q' to quit): ").strip().lower()
        if choice == 'q':
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(consumables):
                selected_item = consumables[idx]
                if isinstance(selected_item, RepairKit):
                    # Show repairable gear
                    repairable = [g for g in character.inventory.gear if isinstance(g, (Weapon, Armour)) and g.durability < g.max_durability]
                    if not repairable:
                        print("No damaged gear to repair.")
                        continue
                    print("\nSelect gear to repair:")
                    for i, gear in enumerate(repairable):
                        print(f"{i + 1}. {gear.name} — Durability: {gear.durability}/{gear.max_durability}")
                    while True:
                        target_choice = input("Select gear (or 'q' to cancel): ").strip().lower()
                        if target_choice == 'q':
                            return
                        try:
                            target_idx = int(target_choice) - 1
                            if 0 <= target_idx < len(repairable):
                                selected_item.selected_target = repairable[target_idx]
                                break
                            else:
                                print("Invalid selection. Try again.")
                        except ValueError:
                            print("Please enter a number or 'q'.")
                character.use_consumable(selected_item)
                break
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a number or 'q'.")

def fight_enemy(character: Character) -> bool:
    """Simulate a fight between the player character and an enemy."""
    enemy_class = random_choice(list(CharacterClass))
    enemy = Character(name=f"Enemy {enemy_class.value}", char_class=enemy_class)
    print(f"\nA wild {enemy.name} appears!")
    result: CombatResult = combat(character, enemy, NormalDamage())
    if result.winner == character:
        print(f"\nYou defeated {enemy.name} in {result.turn_count} turns!")
        logger.info("%s won against %s in %d turns.", character.name, enemy.name, result.turn_count)
        character.gain_xp(enemy.xp_reward_base * enemy.level)
        loot_room(character, result.defeated.inventory, header=f"You search {enemy.name}'s remains...")
        return True  # Player won
    else:
        print(f"\nYou were defeated by {enemy.name}. Game Over.")
        logger.info("%s was defeated by %s.", character.name, enemy.name)
        return False  # Player lost

def game_loop(character: Character) -> None:
    """Main game loop for the IronVault engine."""
    while True:
        show_character_status(character)
        print("\nWhat would you like to do?")
        print("1. Fight an enemy")
        print("2. Loot a room")
        print("3. Equip gear")
        print("4. Use consumable")
        print("5. Save game")
        print("6. Load game")
        print("7. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == '1':
            if not fight_enemy(character):
                break  # Game over
        elif choice == '2':
            loot_room(character, character.inventory)  # Simulate looting a room with random items
        elif choice == '3':
            equip_menu(character)
        elif choice == '4':
            consumable_menu(character)
        elif choice == '5':
            filename = input("Enter filename to save: ").strip()
            save_game(character, filename)
        elif choice == '6':
            print("Loading game available in main menu only. Please restart the game to load a save.")
        elif choice == '7':
            save_choice = input("Save before exiting? (y/n): ").strip().lower()
            if save_choice == 'y':
                filename = input("Enter filename to save: ").strip()
                save_game(character, filename)
            print("Exiting game. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

def run() -> None:
    """Entry point for the IronVault engine."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
    )
    print("Welcome to IronVault!")
    while True:
        print("\nWhat would you like to do?")
        print("1. New Game")
        print("2. Load Game")
        print("3. Exit")

        choice = input("Enter your choice: ").strip()
        if choice == '1':
            # Start a new game
            name = input("Enter your character's name: ").strip()
            print("Choose your class:")
            for idx, char_class in enumerate(CharacterClass):
                print(f"{idx + 1}. {char_class.value}")
            while True:
                class_choice = input("Enter the number of your chosen class: ").strip()
                try:
                    class_idx = int(class_choice) - 1
                    if 0 <= class_idx < len(CharacterClass):
                        char_class = list(CharacterClass)[class_idx]
                        break
                    else:
                        print("Invalid selection. Try again.")
                except ValueError:
                    print("Please enter a valid number.")
            character = Character(name=name, char_class=char_class)
            starter_weapon = Weapon(name="Worn Shortsword", rarity=Rarity.COMMON)
            character.inventory.add_item(starter_weapon)
            character.equip_gear(starter_weapon)
            print(f"\nYou grasp your {starter_weapon.name} and step into the dungeon.")
            logger.info("New game started with character: %s, Class: %s,Inventory: %s", character.name, character.char_class.value, character.inventory)
            game_loop(character)
            break  # Exit after the game loop ends
        elif choice == '2':
            # Load a saved game
            filename = input("Enter the filename of your saved game: ").strip()
            try:
                character = load_game(filename)
                logger.info("Game loaded successfully from %s.", filename)
                game_loop(character)
                break
            except CorruptSaveError as e:
                print(f"Could not load save: {e}")
                logger.error("Corrupt save file: %s", filename)
                continue  # Restart the menu on error
            except Exception as e:
                logger.error("Error occurred while loading game: %s", e)
                continue  # Restart the menu on error
        elif choice == '3':
            print("Exiting game. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")