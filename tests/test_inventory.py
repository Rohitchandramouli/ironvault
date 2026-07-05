"""
Tests for inventory.py — add_item(), remove_item(), dunders, loot_drop().
"""
import pytest
from Ironvault.items import Item, Gear, Consumable, Weapon, Armour, Potion, Rarity
from Ironvault.inventory import Inventory, InventoryFullError, ItemNotFoundError


def test_add_item_routes_gear_to_gear_list(standard_inventory, common_weapon):
    """add_item() routes Gear subclasses to the internal _gear list."""
    standard_inventory.add_item(common_weapon)
    assert common_weapon in standard_inventory.gear


def test_add_item_routes_consumable_to_consumables_list(standard_inventory, potion):
    """add_item() routes Consumable subclasses to the internal _consumables list."""
    standard_inventory.add_item(potion)
    assert potion in standard_inventory.consumables


def test_add_item_raises_inventory_full_error_when_weight_exceeded(
    small_inventory, common_weapon
):
    """add_item() raises InventoryFullError when total weight exceeds max_weight."""
    with pytest.raises(InventoryFullError):
        small_inventory.add_item(common_weapon)


def test_remove_item_raises_item_not_found_error_when_absent(
    standard_inventory, common_weapon
):
    """remove_item() raises ItemNotFoundError when item is not in inventory."""
    with pytest.raises(ItemNotFoundError):
        standard_inventory.remove_item(common_weapon)


def test_total_weight_updates_after_add_and_remove(
    standard_inventory, common_weapon
):
    """total_weight correctly reflects additions and removals."""
    initial_weight = standard_inventory.total_weight
    standard_inventory.add_item(common_weapon)
    assert standard_inventory.total_weight == pytest.approx(
        initial_weight + common_weapon.weight, rel=1e-3
    )
    standard_inventory.remove_item(common_weapon)
    assert standard_inventory.total_weight == pytest.approx(initial_weight, rel=1e-3)


def test_len_returns_combined_count(standard_inventory, common_weapon, potion):
    """__len__ returns total count across both gear and consumables lists."""
    standard_inventory.add_item(common_weapon)
    standard_inventory.add_item(potion)
    assert len(standard_inventory) == 2


def test_contains_finds_items_across_both_lists(
    standard_inventory, common_weapon, potion
):
    """__contains__ returns True for items in either gear or consumables list."""
    standard_inventory.add_item(common_weapon)
    standard_inventory.add_item(potion)
    assert common_weapon in standard_inventory
    assert potion in standard_inventory


def test_iter_yields_gear_first_then_consumables(
    standard_inventory, common_weapon, potion
):
    """__iter__ yields all gear items before any consumables."""
    standard_inventory.add_item(common_weapon)
    standard_inventory.add_item(potion)
    items = list(standard_inventory)
    gear_indices = [i for i, item in enumerate(items) if isinstance(item, Gear)]
    consumable_indices = [i for i, item in enumerate(items) if isinstance(item, Consumable)]
    assert all(g < c for g in gear_indices for c in consumable_indices)


def test_loot_drop_yields_item_instances(standard_inventory):
    """loot_drop() yields only Item instances."""
    for item in standard_inventory.loot_drop():
        assert isinstance(item, Item)


def test_loot_drop_yields_within_expected_count_range(standard_inventory):
    """loot_drop() yields between 1 and 5 items."""
    items = list(standard_inventory.loot_drop())
    assert 1 <= len(items) <= 5