"""Cartridge registry - tracks all cartridges ever used"""

import toml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class CartridgeRegistryEntry:
    """Represents a cartridge in the registry"""
    
    def __init__(self, uuid: str, game_name: str, game_id: str):
        self.uuid = uuid
        self.game_name = game_name
        self.game_id = game_id
        self.total_playtime = 0  # seconds
        self.last_played = ""
        self.play_count = 0
        self.is_inserted = False
        self.last_mount_point = ""
        self.first_seen = datetime.now().isoformat()
        self.icon_path = ""  # Optional custom icon
    
    def update_from_cartridge(self, cartridge):
        """Update entry from a live cartridge"""
        self.game_name = cartridge.metadata.game_name
        self.game_id = cartridge.metadata.game_id
        self.total_playtime = cartridge.metadata.total_playtime
        self.last_played = cartridge.metadata.last_played
        self.play_count = cartridge.metadata.play_count
        self.is_inserted = True
        self.last_mount_point = str(cartridge.mount_path)  # Convert Path to string
    
    def to_dict(self) -> dict:
        """Convert to dictionary for TOML"""
        return {
            "uuid": self.uuid,
            "game_name": self.game_name,
            "game_id": self.game_id,
            "total_playtime": self.total_playtime,
            "last_played": self.last_played,
            "play_count": self.play_count,
            "is_inserted": self.is_inserted,
            "last_mount_point": self.last_mount_point,
            "first_seen": self.first_seen,
            "icon_path": self.icon_path
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CartridgeRegistryEntry':
        """Create entry from dictionary"""
        entry = cls(
            uuid=data["uuid"],
            game_name=data["game_name"],
            game_id=data["game_id"]
        )
        entry.total_playtime = data.get("total_playtime", 0)
        entry.last_played = data.get("last_played", "")
        entry.play_count = data.get("play_count", 0)
        entry.is_inserted = data.get("is_inserted", False)
        entry.last_mount_point = data.get("last_mount_point", "")
        entry.first_seen = data.get("first_seen", datetime.now().isoformat())
        entry.icon_path = data.get("icon_path", "")
        return entry


class CartridgeRegistry:
    """Manages the registry of all known cartridges"""
    
    def __init__(self, config_dir: Path):
        self.registry_file = config_dir / "cartridge_registry.toml"
        self.entries: Dict[str, CartridgeRegistryEntry] = {}
        self._load()
    
    def _load(self):
        """Load registry from file"""
        if not self.registry_file.exists():
            print("No cartridge registry found, creating new one")
            return
        
        try:
            data = toml.load(self.registry_file)
            
            # Clear existing entries
            self.entries.clear()
            
            for entry_data in data.get("cartridges", []):
                entry = CartridgeRegistryEntry.from_dict(entry_data)
                self.entries[entry.uuid] = entry
            
            print(f"Loaded {len(self.entries)} cartridge(s) from registry")
        except Exception as e:
            print(f"Error loading cartridge registry: {e}")
    
    def _save(self):
        """Save registry to file"""
        try:
            # Ensure directory exists
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "cartridges": [entry.to_dict() for entry in self.entries.values()]
            }
            
            with open(self.registry_file, 'w') as f:
                toml.dump(data, f)
            
            print(f"Saved {len(self.entries)} cartridge(s) to registry")
        except Exception as e:
            print(f"Error saving cartridge registry: {e}")
    
    def add_or_update(self, cartridge) -> bool:
        """Add or update a cartridge in the registry
        
        Args:
            cartridge: Cartridge object
            
        Returns:
            True if this is a new cartridge, False if updated
        """
        uuid = cartridge.metadata.uuid
        is_new = uuid not in self.entries
        
        if is_new:
            entry = CartridgeRegistryEntry(
                uuid=uuid,
                game_name=cartridge.metadata.game_name,
                game_id=cartridge.metadata.game_id
            )
            self.entries[uuid] = entry
            print(f"Added new cartridge to registry: {cartridge.metadata.game_name}")
        else:
            entry = self.entries[uuid]
        
        entry.update_from_cartridge(cartridge)
        self._save()
        
        return is_new
    
    def mark_ejected(self, uuid: str):
        """Mark a cartridge as ejected (not inserted)
        
        Args:
            uuid: Cartridge UUID
        """
        if uuid in self.entries:
            self.entries[uuid].is_inserted = False
            self._save()
            print(f"Marked cartridge as ejected: {self.entries[uuid].game_name}")
    
    def get_entry(self, uuid: str) -> Optional[CartridgeRegistryEntry]:
        """Get a registry entry by UUID
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            Registry entry or None
        """
        return self.entries.get(uuid)
    
    def get_all_entries(self) -> List[CartridgeRegistryEntry]:
        """Get all registry entries
        
        Returns:
            List of all cartridge entries
        """
        return list(self.entries.values())
    
    def get_inserted_entries(self) -> List[CartridgeRegistryEntry]:
        """Get currently inserted cartridge entries
        
        Returns:
            List of inserted cartridge entries
        """
        return [entry for entry in self.entries.values() if entry.is_inserted]
    
    def remove_entry(self, uuid: str) -> bool:
        """Remove a cartridge from the registry
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            True if removed, False if not found
        """
        if uuid in self.entries:
            entry = self.entries[uuid]
            del self.entries[uuid]
            self._save()
            print(f"Removed cartridge from registry: {entry.game_name}")
            return True
        return False
    
    def get_total_games(self) -> int:
        """Get total number of games in registry"""
        return len(self.entries)
    
    def get_total_playtime(self) -> int:
        """Get combined playtime across all games (in seconds)"""
        return sum(entry.total_playtime for entry in self.entries.values())

