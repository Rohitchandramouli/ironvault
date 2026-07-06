"""
Tests for save/load — Character serialization, save_game(), load_game(), CorruptSaveError.
"""
import json
import os
import pytest
from Ironvault.character import Character, CharacterClass
from Ironvault.items import Item
from Ironvault.main import save_game, load_game, CorruptSaveError


def test_character_to_dict_from_dict_round_trips_correctly(warrior, common_weapon):
    """Character.to_dict() / from_dict() preserves all state exactly."""
    warrior.inventory.add_item(common_weapon)
    warrior.equip_gear(common_weapon)
    warrior.gain_xp(100)
    original_dict = warrior.to_dict()
    reconstructed = Character.from_dict(original_dict)
    assert reconstructed.name == warrior.name
    assert reconstructed.char_class == warrior.char_class
    assert reconstructed.level == warrior.level
    assert reconstructed.current_xp == warrior.current_xp
    assert reconstructed.health == warrior.health
    assert reconstructed.base_health == warrior.base_health
    assert reconstructed.base_attack == warrior.base_attack
    assert reconstructed.base_defense == warrior.base_defense
    assert reconstructed.equipped_weapon is not None
    assert reconstructed.equipped_weapon.name == common_weapon.name


def test_save_game_load_game_produces_identical_character(
    warrior, common_weapon, tmp_path
):
    """save_game() / load_game() produces a Character identical to the original."""
    warrior.inventory.add_item(common_weapon)
    warrior.equip_gear(common_weapon)
    filepath = str(tmp_path / "test_save.json")
    save_game(warrior, filepath)
    loaded = load_game(filepath)
    assert loaded.name == warrior.name
    assert loaded.char_class == warrior.char_class
    assert loaded.level == warrior.level
    assert loaded.health == warrior.health
    assert loaded.equipped_weapon is not None
    assert loaded.equipped_weapon.name == warrior.equipped_weapon.name


def test_load_game_raises_corrupt_save_error_on_malformed_json(tmp_path):
    """load_game() raises CorruptSaveError when JSON is malformed."""
    filepath = str(tmp_path / "corrupt_save.json")
    with open(filepath, 'w') as f:
        f.write("this is not valid json {{{")
    with pytest.raises(CorruptSaveError):
        load_game(filepath)