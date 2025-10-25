"""Main service entry point for Physica"""

import sys
import signal
import argparse
import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from pathlib import Path

try:
    from .config import Config
    from .cartridge_scanner import CartridgeScanner
    from .game_launcher import GameLauncher
    from .dbus_service import PhysicaDBusService
    from .cartridge_registry import CartridgeRegistry
except ImportError:
    from config import Config
    from cartridge_scanner import CartridgeScanner
    from game_launcher import GameLauncher
    from dbus_service import PhysicaDBusService
    from cartridge_registry import CartridgeRegistry


class PhysicaService:
    """Main service manager"""
    
    def __init__(self, debug: bool = False):
        """Initialize Physica service
        
        Args:
            debug: Enable debug output
        """
        self.debug = debug
        self.running = False
        
        print("=== Physica Service Starting ===\n")
        
        # Load configuration
        print("Loading configuration...")
        self.config = Config()
        print(f"  Mount base: {self.config.mount_base}")
        print(f"  Scan interval: {self.config.scan_interval}s")
        print(f"  Default Wine: {self.config.default_wine_version}")
        print(f"  Config dir: {self.config.config_dir}")
        print()
        
        # Initialize components
        print("Initializing components...")
        self.registry = CartridgeRegistry(Path(self.config.config_dir))
        self.scanner = CartridgeScanner(self.config)
        self.launcher = GameLauncher(self.config, self.scanner)
        print("✓ Components initialized\n")
        
        # Setup D-Bus
        print("Setting up D-Bus service...")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        
        # Use session bus for development, system bus for production
        if self.debug:
            print("Debug mode: Using session bus")
            self.bus = dbus.SessionBus()
        else:
            try:
                self.bus = dbus.SystemBus()
            except dbus.exceptions.DBusException:
                print("Warning: Could not connect to system bus, trying session bus...")
                self.bus = dbus.SessionBus()
        
        try:
            bus_name = dbus.service.BusName(
                PhysicaDBusService.BUS_NAME,
                self.bus
            )
            self.dbus_service = PhysicaDBusService(
                self.scanner,
                self.launcher,
                self.registry,
                bus_name
            )
            bus_type = 'session' if self.debug else 'system'
            print(f"✓ D-Bus service registered: {PhysicaDBusService.BUS_NAME}")
            print(f"  Object path: {PhysicaDBusService.OBJECT_PATH}")
            print(f"  Bus type: {bus_type}\n")
        except dbus.exceptions.DBusException as e:
            print(f"Error: Failed to register D-Bus service: {e}")
            print("Make sure no other instance is running.")
            print("Tip: Check for existing process: ps aux | grep physica")
            sys.exit(1)
        
        # Setup GLib main loop
        self.main_loop = GLib.MainLoop()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Initial scan
        print("Performing initial cartridge scan...")
        inserted, removed = self.scanner.refresh_cartridges()
        cartridges = self.scanner.list_cartridges()
        print(f"  Found {len(cartridges)} cartridge(s)\n")
        
        # Update registry with initially detected cartridges
        for cartridge in cartridges:
            is_new = self.registry.add_or_update(cartridge)
            if is_new:
                print(f"  ✨ First time seeing this cartridge!")
            print(f"  📀 {cartridge.metadata.game_name}")
        
        if cartridges:
            print()
        
        # Setup periodic tasks
        self._setup_timers()
    
    def _setup_timers(self):
        """Setup periodic timer callbacks"""
        # Cartridge scanning timer
        scan_interval_ms = self.config.scan_interval * 1000
        GLib.timeout_add(scan_interval_ms, self._scan_timer_callback)
        
        # Running games check timer (every 5 seconds)
        GLib.timeout_add(5000, self._game_check_timer_callback)
    
    def _scan_timer_callback(self) -> bool:
        """Periodic cartridge scan callback
        
        Returns:
            True to keep timer active
        """
        if self.debug:
            print("Scanning for cartridge changes...")
        
        try:
            inserted, removed = self.scanner.refresh_cartridges()
            
            # Emit signals for inserted cartridges
            for uuid in inserted:
                cartridge = self.scanner.get_cartridge(uuid)
                if cartridge:
                    print(f"📀 Cartridge inserted: {cartridge.metadata.game_name}")
                    
                    # Update registry
                    is_new = self.registry.add_or_update(cartridge)
                    if is_new:
                        print(f"  ✨ First time seeing this cartridge!")
                    
                    self.dbus_service.CartridgeInserted(uuid, cartridge.metadata.game_name)
                    
                    # Auto-launch if enabled for this cartridge
                    if cartridge.metadata.auto_launch:
                        delay = self.config.auto_launch_delay
                        print(f"  ⏱️  Auto-launch enabled, waiting {delay} seconds...")
                        # Schedule auto-launch after delay
                        GLib.timeout_add_seconds(
                            delay,
                            self._auto_launch_callback,
                            uuid
                        )
            
            # Emit signals for removed cartridges
            for uuid in removed:
                print(f"📤 Cartridge removed: {uuid}")
                # Mark as ejected in registry
                self.registry.mark_ejected(uuid)
                self.dbus_service.CartridgeRemoved(uuid)
        
        except Exception as e:
            print(f"Error during cartridge scan: {e}")
        
        return True  # Keep timer running
    
    def _auto_launch_callback(self, uuid: str) -> bool:
        """Auto-launch game after cartridge insertion delay
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            False to cancel the timer (one-shot)
        """
        try:
            cartridge = self.scanner.get_cartridge(uuid)
            if not cartridge:
                print(f"⚠️  Auto-launch canceled: Cartridge {uuid} no longer available")
                return False
            
            # Check if game is already running
            if self.launcher.is_game_running(uuid):
                print(f"⚠️  Auto-launch canceled: Game already running")
                return False
            
            print(f"🚀 Auto-launching: {cartridge.metadata.game_name}")
            success = self.launcher.launch_game(uuid)
            
            if success:
                print(f"  ✓ Auto-launch successful")
                self.dbus_service.GameLaunched(uuid, cartridge.metadata.game_name)
            else:
                print(f"  ✗ Auto-launch failed")
        
        except Exception as e:
            print(f"Error during auto-launch: {e}")
            import traceback
            traceback.print_exc()
        
        return False  # One-shot timer
    
    def _game_check_timer_callback(self) -> bool:
        """Periodic running games check callback
        
        Returns:
            True to keep timer active
        """
        try:
            stopped_uuids = self.launcher.check_running_games()
            
            # Emit signals for stopped games
            for uuid in stopped_uuids:
                cartridge = self.scanner.get_cartridge(uuid)
                if cartridge:
                    session_time = cartridge.metadata.total_playtime  # This was just updated
                    print(f"🎮 Game stopped: {cartridge.metadata.game_name}")
                    self.dbus_service.GameStopped(uuid, session_time)
        
        except Exception as e:
            print(f"Error checking running games: {e}")
        
        return True  # Keep timer running
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        print(f"\n\nReceived signal {signum}, shutting down...")
        self.shutdown()
    
    def run(self):
        """Run the service main loop"""
        self.running = True
        print("=== Physica Service Running ===")
        print("Press Ctrl+C to stop\n")
        
        try:
            self.main_loop.run()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the service"""
        if not self.running:
            return
        
        print("\n=== Shutting Down ===")
        self.running = False
        
        # Stop any running games
        running_games = list(self.launcher.running_games.keys())
        if running_games:
            print(f"Stopping {len(running_games)} running game(s)...")
            for uuid in running_games:
                self.launcher.stop_game(uuid)
        
        # Quit main loop
        if self.main_loop.is_running():
            self.main_loop.quit()
        
        print("✓ Service stopped")
        sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Physica Game Cartridge Service")
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    try:
        service = PhysicaService(debug=args.debug)
        service.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

