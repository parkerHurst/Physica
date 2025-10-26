"""D-Bus client for Physica GTK app"""

import dbus
import dbus.mainloop.glib
from typing import List, Dict, Optional, Callable


class PhysicaDBusClient:
    """Client for communicating with Physica service via D-Bus"""
    
    BUS_NAME = "org.physicaapp.Manager"
    OBJECT_PATH = "/org/physicaapp/Manager"
    INTERFACE_NAME = "org.physicaapp.Manager"
    
    def __init__(self):
        """Initialize D-Bus client"""
        try:
            # Initialize D-Bus main loop integration with GTK
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            
            self.bus = dbus.SessionBus()
            self.proxy = self.bus.get_object(self.BUS_NAME, self.OBJECT_PATH)
            self.interface = dbus.Interface(self.proxy, self.INTERFACE_NAME)
            print("✓ Connected to Physica service")
        except dbus.exceptions.DBusException as e:
            print(f"⚠ Could not connect to Physica service: {e}")
            self.interface = None
    
    def is_connected(self) -> bool:
        """Check if connected to service"""
        return self.interface is not None
    
    # ========== Registry Methods ==========
    
    def get_all_games(self) -> List[Dict]:
        """Get all games from registry (for memory card view)
        
        Returns:
            List of game dictionaries
        """
        if not self.interface:
            return []
        
        try:
            result = self.interface.GetAllGames()
            games = []
            
            for game_dict in result:
                game = {}
                for key, value in game_dict.items():
                    # Extract value from D-Bus variant
                    game[key] = value
                games.append(game)
            
            return games
        except Exception as e:
            print(f"Error getting all games: {e}")
            return []
    
    def get_registry_stats(self) -> Dict:
        """Get registry statistics
        
        Returns:
            Dictionary with total_games, total_playtime, etc.
        """
        if not self.interface:
            return {}
        
        try:
            result = self.interface.GetRegistryStats()
            stats = {}
            for key, value in result.items():
                stats[key] = value
            return stats
        except Exception as e:
            print(f"Error getting registry stats: {e}")
            return {}
    
    def remove_from_registry(self, uuid: str) -> bool:
        """Remove a game from the registry
        
        Args:
            uuid: Game UUID
            
        Returns:
            True if removed successfully
        """
        if not self.interface:
            return False
        
        try:
            return bool(self.interface.RemoveFromRegistry(uuid))
        except Exception as e:
            print(f"Error removing from registry: {e}")
            return False
    
    # ========== Cartridge Methods ==========
    
    def list_cartridges(self) -> List[Dict]:
        """List currently inserted cartridges
        
        Returns:
            List of cartridge dictionaries
        """
        if not self.interface:
            return []
        
        try:
            result = self.interface.ListCartridges()
            cartridges = []
            
            for cart_dict in result:
                cart = {}
                for key, value in cart_dict.items():
                    cart[key] = value
                cartridges.append(cart)
            
            return cartridges
        except Exception as e:
            print(f"Error listing cartridges: {e}")
            return []
    
    def refresh_cartridges(self):
        """Force refresh of cartridge detection"""
        if not self.interface:
            return
        
        try:
            self.interface.RefreshCartridges()
        except Exception as e:
            print(f"Error refreshing cartridges: {e}")
    
    # ========== Game Launch Methods ==========
    
    def launch_game(self, uuid: str) -> bool:
        """Launch a game
        
        Args:
            uuid: Game UUID
            
        Returns:
            True if launched successfully
        """
        if not self.interface:
            return False
        
        try:
            return bool(self.interface.LaunchGame(uuid))
        except Exception as e:
            print(f"Error launching game: {e}")
            return False
    
    def is_game_running(self, uuid: str) -> bool:
        """Check if a game is running
        
        Args:
            uuid: Game UUID
            
        Returns:
            True if game is running
        """
        if not self.interface:
            return False
        
        try:
            return bool(self.interface.IsGameRunning(uuid))
        except Exception as e:
            return False
    
    # ========== Signal Handlers ==========
    
    def connect_cartridge_inserted(self, callback: Callable[[str, str], None]):
        """Connect to CartridgeInserted signal
        
        Args:
            callback: Function to call with (uuid, name) when cartridge inserted
        """
        if not self.interface:
            return
        
        try:
            self.interface.connect_to_signal(
                "CartridgeInserted",
                callback,
                dbus_interface=self.INTERFACE_NAME
            )
        except Exception as e:
            print(f"Error connecting to CartridgeInserted signal: {e}")
    
    def connect_cartridge_removed(self, callback: Callable[[str], None]):
        """Connect to CartridgeRemoved signal
        
        Args:
            callback: Function to call with (uuid) when cartridge removed
        """
        if not self.interface:
            return
        
        try:
            self.interface.connect_to_signal(
                "CartridgeRemoved",
                callback,
                dbus_interface=self.INTERFACE_NAME
            )
        except Exception as e:
            print(f"Error connecting to CartridgeRemoved signal: {e}")
    
    def connect_game_launched(self, callback: Callable[[str, str], None]):
        """Connect to GameLaunched signal
        
        Args:
            callback: Function to call with (uuid, name) when game launches
        """
        if not self.interface:
            return
        
        try:
            self.interface.connect_to_signal(
                "GameLaunched",
                callback,
                dbus_interface=self.INTERFACE_NAME
            )
        except Exception as e:
            print(f"Error connecting to GameLaunched signal: {e}")
    
    def connect_game_stopped(self, callback: Callable[[str, str, int], None]):
        """Connect to GameStopped signal
        
        Args:
            callback: Function to call with (uuid, name, playtime) when game stops
        """
        if not self.interface:
            return
        
        try:
            self.interface.connect_to_signal(
                "GameStopped",
                callback,
                dbus_interface=self.INTERFACE_NAME
            )
        except Exception as e:
            print(f"Error connecting to GameStopped signal: {e}")

