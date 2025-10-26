"""D-Bus service interface for Physica"""

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from typing import List, Dict, Optional


class PhysicaDBusService(dbus.service.Object):
    """D-Bus service for game cartridge management"""
    
    BUS_NAME = "org.physicaapp.Manager"
    OBJECT_PATH = "/org/physicaapp/Manager"
    INTERFACE_NAME = "org.physicaapp.Manager"
    
    def __init__(self, scanner, launcher, registry, bus_name):
        """Initialize D-Bus service
        
        Args:
            scanner: CartridgeScanner instance
            launcher: GameLauncher instance
            registry: CartridgeRegistry instance
            bus_name: D-Bus bus name
        """
        super().__init__(bus_name, self.OBJECT_PATH)
        self.scanner = scanner
        self.launcher = launcher
        self.registry = registry
    
    # ========== Cartridge Management Methods ==========
    
    @dbus.service.method(INTERFACE_NAME, out_signature='aa{sv}')
    def ListCartridges(self) -> List[Dict]:
        """List all detected cartridges
        
        Returns:
            Array of cartridge info dictionaries
        """
        cartridges = self.scanner.list_cartridges_info()
        # Convert to D-Bus compatible format
        return [self._dict_to_dbus(c) for c in cartridges]
    
    @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='a{sv}')
    def GetCartridge(self, uuid: str) -> Dict:
        """Get information about a specific cartridge
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            Cartridge info dictionary or empty dict if not found
        """
        info = self.scanner.get_cartridge_info(uuid)
        if info:
            return self._dict_to_dbus(info)
        return {}
    
    @dbus.service.method(INTERFACE_NAME)
    def RefreshCartridges(self):
        """Force refresh of cartridge registry"""
        inserted, removed = self.scanner.refresh_cartridges()
        
        # Emit signals for changes
        for uuid in inserted:
            cartridge = self.scanner.get_cartridge(uuid)
            if cartridge:
                # Update registry
                self.registry.add_or_update(cartridge)
                self.CartridgeInserted(uuid, cartridge.metadata.game_name)
        
        for uuid in removed:
            # Mark as ejected in registry
            self.registry.mark_ejected(uuid)
            self.CartridgeRemoved(uuid)
    
    @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='b')
    def EjectCartridge(self, uuid: str) -> bool:
        """Safely eject a cartridge
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            True if ejected successfully, False otherwise
        """
        # TODO: Check if game is running
        if self.launcher.is_game_running(uuid):
            print(f"Cannot eject cartridge {uuid}: game is running")
            return False
        
        cartridge = self.scanner.get_cartridge(uuid)
        if not cartridge:
            return False
        
        try:
            # TODO: Implement actual unmount logic
            # For now, just remove from registry
            print(f"Ejecting cartridge: {cartridge.metadata.game_name}")
            # In a real implementation, we'd call:
            # subprocess.run(['udisksctl', 'unmount', '-b', device_path])
            # subprocess.run(['udisksctl', 'power-off', '-b', device_path])
            return True
        except Exception as e:
            print(f"Error ejecting cartridge {uuid}: {e}")
            return False
    
    # ========== Registry Methods ==========
    
    @dbus.service.method(INTERFACE_NAME, out_signature='aa{sv}')
    def GetAllGames(self) -> List[Dict]:
        """Get all games from the registry (memory card view)
        
        Returns:
            Array of game info dictionaries from registry
        """
        # Force refresh registry from file to ensure we have latest data
        self.registry._load()
        
        entries = self.registry.get_all_entries()
        result = []
        
        for entry in entries:
            game_dict = {
                "uuid": entry.uuid,
                "game_name": entry.game_name,
                "game_id": entry.game_id,
                "total_playtime": dbus.Int64(entry.total_playtime),
                "last_played": entry.last_played,
                "play_count": dbus.Int32(entry.play_count),
                "is_inserted": entry.is_inserted,
                "last_mount_point": entry.last_mount_point,
                "first_seen": entry.first_seen,
                "icon_path": entry.icon_path
            }
            result.append(self._dict_to_dbus(game_dict))
        
        return result
    
    @dbus.service.method(INTERFACE_NAME, out_signature='a{sv}')
    def GetRegistryStats(self) -> Dict:
        """Get overall registry statistics
        
        Returns:
            Dictionary with total_games, total_playtime, etc.
        """
        stats = {
            "total_games": dbus.Int32(self.registry.get_total_games()),
            "total_playtime": dbus.Int64(self.registry.get_total_playtime()),
            "inserted_count": dbus.Int32(len(self.registry.get_inserted_entries()))
        }
        return self._dict_to_dbus(stats)
    
    @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='b')
    def RemoveFromRegistry(self, uuid: str) -> bool:
        """Remove a game from the registry
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            True if removed, False if not found
        """
        return self.registry.remove_entry(uuid)
    
    # ========== Game Launching Methods ==========
    
    @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='b')
    def LaunchGame(self, uuid: str) -> bool:
        """Launch a game from a cartridge
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            True if launched successfully, False otherwise
        """
        print(f"[D-Bus] LaunchGame called for UUID: {uuid}")
        try:
            print(f"[D-Bus] Calling launcher.launch_game...")
            success = self.launcher.launch_game(uuid)
            print(f"[D-Bus] Launcher returned: {success}")
            if success:
                cartridge = self.scanner.get_cartridge(uuid)
                if cartridge:
                    self.GameLaunched(uuid, cartridge.metadata.game_name)
            return success
        except Exception as e:
            print(f"[D-Bus] Error launching game {uuid}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='b')
    def IsGameRunning(self, uuid: str) -> bool:
        """Check if a game is currently running
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            True if game is running, False otherwise
        """
        return self.launcher.is_game_running(uuid)
    
    @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='b')
    def StopGame(self, uuid: str) -> bool:
        """Stop a running game
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            True if stopped successfully, False otherwise
        """
        return self.launcher.stop_game(uuid)
    
    # ========== Metadata Methods ==========
    
    @dbus.service.method(INTERFACE_NAME, in_signature='sa{sv}', out_signature='b')
    def UpdateMetadata(self, uuid: str, metadata: Dict) -> bool:
        """Update cartridge metadata
        
        Args:
            uuid: Cartridge UUID
            metadata: Dictionary of metadata fields to update
            
        Returns:
            True if updated successfully, False otherwise
        """
        cartridge = self.scanner.get_cartridge(uuid)
        if not cartridge:
            return False
        
        try:
            # Update metadata fields
            for key, value in metadata.items():
                if hasattr(cartridge.metadata, key):
                    setattr(cartridge.metadata, key, value)
            
            # Save to file
            cartridge.save_metadata()
            return True
        except Exception as e:
            print(f"Error updating metadata for {uuid}: {e}")
            return False
    
    @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='i')
    def GetPlaytime(self, uuid: str) -> int:
        """Get total playtime for a cartridge
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            Total playtime in seconds, or 0 if not found
        """
        cartridge = self.scanner.get_cartridge(uuid)
        if cartridge:
            return cartridge.metadata.total_playtime
        return 0
    
    # ========== D-Bus Signals ==========
    
    @dbus.service.signal(INTERFACE_NAME, signature='ss')
    def CartridgeInserted(self, uuid: str, name: str):
        """Signal emitted when a cartridge is inserted
        
        Args:
            uuid: Cartridge UUID
            name: Game name
        """
        pass
    
    @dbus.service.signal(INTERFACE_NAME, signature='s')
    def CartridgeRemoved(self, uuid: str):
        """Signal emitted when a cartridge is removed
        
        Args:
            uuid: Cartridge UUID
        """
        pass
    
    @dbus.service.signal(INTERFACE_NAME, signature='ss')
    def GameLaunched(self, uuid: str, name: str):
        """Signal emitted when a game is launched
        
        Args:
            uuid: Cartridge UUID
            name: Game name
        """
        pass
    
    @dbus.service.signal(INTERFACE_NAME, signature='si')
    def GameStopped(self, uuid: str, playtime_session: int):
        """Signal emitted when a game stops
        
        Args:
            uuid: Cartridge UUID
            playtime_session: Seconds played in this session
        """
        pass
    
    # ========== Helper Methods ==========
    
    def _dict_to_dbus(self, data: Dict) -> Dict:
        """Convert Python dict to D-Bus compatible dict
        
        Args:
            data: Python dictionary
            
        Returns:
            D-Bus compatible dictionary
        """
        result = {}
        for key, value in data.items():
            # Convert None to empty string for D-Bus
            if value is None:
                value = ""
            # Convert lists
            elif isinstance(value, list):
                value = dbus.Array(value, signature='s')
            # Convert large integers to Int64 (avoid Int32 overflow)
            elif isinstance(value, int):
                # D-Bus Int32 range: -2,147,483,648 to 2,147,483,647
                if value < -2147483648 or value > 2147483647:
                    value = dbus.Int64(value)
                else:
                    value = dbus.Int32(value)
            # Keep other basic types as is
            result[key] = value
        return result

