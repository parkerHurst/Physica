"""Game launcher with Proton/Wine support"""

import os
import subprocess
import psutil
import time
import shutil
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

try:
    from .config import Config
    from .cartridge_scanner import CartridgeScanner
except ImportError:
    from config import Config
    from cartridge_scanner import CartridgeScanner


class ProtonFinder:
    """Find and manage Proton/Wine installations"""
    
    def __init__(self, config: Config):
        """Initialize Proton finder
        
        Args:
            config: Service configuration
        """
        self.config = config
        self._proton_cache: Dict[str, Path] = {}
    
    def find_proton(self, version: str) -> Optional[Path]:
        """Find Proton installation by version name
        
        Args:
            version: Proton version (e.g., "GE-Proton8-14")
            
        Returns:
            Path to Proton installation or None if not found
        """
        # Check cache
        if version in self._proton_cache:
            return self._proton_cache[version]
        
        # Search in configured paths
        for search_path in self.config.wine_search_paths:
            search_path = Path(search_path)
            if not search_path.exists():
                continue
            
            # Look for version directory
            proton_path = search_path / version
            if proton_path.exists():
                # Verify it has the proton script
                proton_script = proton_path / "proton"
                if proton_script.exists():
                    self._proton_cache[version] = proton_path
                    print(f"Found Proton {version} at {proton_path}")
                    return proton_path
        
        print(f"Warning: Proton version {version} not found")
        return None
    
    def list_available_proton(self) -> list[str]:
        """List all available Proton versions
        
        Returns:
            List of Proton version names
        """
        versions = []
        
        for search_path in self.config.wine_search_paths:
            search_path = Path(search_path)
            if not search_path.exists():
                continue
            
            # Look for directories with proton script
            for entry in search_path.iterdir():
                if entry.is_dir():
                    proton_script = entry / "proton"
                    if proton_script.exists():
                        versions.append(entry.name)
        
        return sorted(versions)


class RunningGame:
    """Represents a running game process"""
    
    def __init__(self, uuid: str, game_name: str, process: psutil.Process, start_time: float):
        """Initialize running game
        
        Args:
            uuid: Cartridge UUID
            game_name: Game name
            process: psutil Process object
            start_time: Start timestamp
        """
        self.uuid = uuid
        self.game_name = game_name
        self.process = process
        self.start_time = start_time
    
    def is_running(self) -> bool:
        """Check if game process is still running
        
        Returns:
            True if running, False otherwise
        """
        try:
            return self.process.is_running() and self.process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def get_playtime(self) -> int:
        """Get current session playtime in seconds
        
        Returns:
            Seconds played in this session
        """
        return int(time.time() - self.start_time)
    
    def terminate(self):
        """Terminate the game process"""
        try:
            self.process.terminate()
            # Wait up to 5 seconds for graceful shutdown
            self.process.wait(timeout=5)
        except psutil.TimeoutExpired:
            # Force kill if still running
            self.process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


class GameLauncher:
    """Manages game launching and tracking"""
    
    def __init__(self, config: Config, scanner: CartridgeScanner):
        """Initialize game launcher
        
        Args:
            config: Service configuration
            scanner: CartridgeScanner instance
        """
        self.config = config
        self.scanner = scanner
        self.proton_finder = ProtonFinder(config)
        self.running_games: Dict[str, RunningGame] = {}  # uuid -> RunningGame
    
    def launch_game(self, uuid: str) -> bool:
        """Launch a game from a cartridge
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            True if launched successfully, False otherwise
        """
        print(f"[Launcher] launch_game called for UUID: {uuid}")
        
        # Check if already running
        if self.is_game_running(uuid):
            print(f"[Launcher] Game {uuid} is already running")
            return False
        
        print(f"[Launcher] Getting cartridge from scanner...")
        # Get cartridge
        cartridge = self.scanner.get_cartridge(uuid)
        print(f"[Launcher] Cartridge result: {cartridge}")
        if not cartridge:
            print(f"[Launcher] Cartridge {uuid} not found")
            return False
        
        meta = cartridge.metadata
        
        print(f"Launching game: {meta.game_name}")
        print(f"  Executable: {meta.executable}")
        print(f"  Wine Version: {meta.wine_version}")
        print(f"  Platform: {meta.platform}")
        
        # Check if executable exists
        try:
            exe_path = meta.get_executable_path()
            if not exe_path.exists():
                print(f"Error: Executable not found at {exe_path}")
                return False
        except Exception as e:
            print(f"Error getting executable path: {e}")
            return False
        
        # Launch based on platform
        if meta.platform == "windows" and meta.needs_wine:
            return self._launch_windows_game(cartridge)
        else:
            # Native Linux games (future support)
            print(f"Platform {meta.platform} not yet supported")
            return False
    
    def _launch_windows_game(self, cartridge) -> bool:
        """Launch a Windows game using Proton/Wine
        
        Args:
            cartridge: Cartridge instance
            
        Returns:
            True if launched successfully, False otherwise
        """
        meta = cartridge.metadata
        
        # Find Proton installation
        proton_path = self.proton_finder.find_proton(meta.wine_version)
        if not proton_path:
            print(f"Error: Proton version {meta.wine_version} not found")
            # Try default version
            proton_path = self.proton_finder.find_proton(self.config.default_wine_version)
            if not proton_path:
                print(f"Error: Default Proton version also not found")
                return False
            print(f"Using default Proton version instead: {self.config.default_wine_version}")
        
        # Get paths
        exe_path = meta.get_executable_path()
        prefix_path = meta.get_prefix_path()
        working_dir = meta.get_working_directory_path()
        
        # Ensure prefix directory exists
        prefix_path.mkdir(parents=True, exist_ok=True)
        
        # Restore saves from cartridge to local prefix
        print("  Syncing saves from cartridge...")
        self._sync_saves_from_cartridge(cartridge)
        
        # Set up environment
        env = os.environ.copy()
        env['WINEPREFIX'] = str(prefix_path)
        env['STEAM_COMPAT_DATA_PATH'] = str(prefix_path.parent)
        env['STEAM_COMPAT_CLIENT_INSTALL_PATH'] = str(Path.home() / ".steam/steam")
        
        # Ensure DISPLAY is set for graphics
        if 'DISPLAY' not in env:
            env['DISPLAY'] = ':0'  # Default display
        
        # Enable Proton logging for debugging
        env['PROTON_LOG'] = '1'
        env['PROTON_LOG_DIR'] = str(prefix_path)
        
        # Apply custom environment variables from metadata
        if meta.env_vars:
            print(f"  Custom environment variables:")
            for key, value in meta.env_vars.items():
                env[key] = str(value)
                print(f"    {key}={value}")
        
        # Construct command
        proton_script = proton_path / "proton"
        cmd = [str(proton_script), "run", str(exe_path)]
        
        # Add launch arguments
        if meta.launch_args:
            cmd.extend(meta.launch_args)
        
        print(f"  Command: {' '.join(cmd)}")
        print(f"  Working Directory: {working_dir}")
        print(f"  WINEPREFIX: {prefix_path}")
        
        try:
            # Launch the game
            # Redirect output to a log file so we can see errors
            log_file_path = prefix_path / "game_launch.log"
            log_file = open(log_file_path, 'w')
            
            print(f"  Output redirected to: {log_file_path}")
            
            process = subprocess.Popen(
                cmd,
                cwd=str(working_dir),
                env=env,
                stdin=subprocess.DEVNULL,  # Close stdin so Proton doesn't wait
                stdout=log_file,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                start_new_session=False  # Don't detach - keep connected
            )
            
            # Wait longer for initialization (especially first launch)
            print(f"  Waiting for game to initialize...")
            time.sleep(5)
            
            if process.poll() is not None:
                # Process already exited
                print(f"✗ Game process exited immediately (exit code: {process.returncode})")
                print(f"  Check Proton logs at: {prefix_path}/")
                return False
            
            # Wrap in psutil for better process management
            ps_process = psutil.Process(process.pid)
            
            # Track the running game
            running_game = RunningGame(
                uuid=meta.uuid,
                game_name=meta.game_name,
                process=ps_process,
                start_time=time.time()
            )
            self.running_games[meta.uuid] = running_game
            
            print(f"✓ Game launched successfully (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"Error launching game: {e}")
            return False
    
    def _sync_saves_from_cartridge(self, cartridge) -> None:
        """Sync save files from cartridge to local prefix
        
        Args:
            cartridge: Cartridge instance
        """
        try:
            savedata_dir = Path(cartridge.mount_path) / "savedata"
            if not savedata_dir.exists():
                print("  No savedata directory on cartridge")
                return
            
            # Check if we have configured save paths
            if not cartridge.metadata.save_paths:
                print("  Warning: No save_paths configured in metadata.toml")
                return
            
            prefix_path = cartridge.metadata.get_prefix_path()
            total_files = 0
            
            # Restore saves for each configured path
            for save_path_str in cartridge.metadata.save_paths:
                # Construct full path in prefix
                save_path = prefix_path / save_path_str
                
                # Construct corresponding path in savedata (preserves directory structure)
                cartridge_save_path = savedata_dir / save_path_str
                
                if not cartridge_save_path.exists():
                    continue  # Skip if this save location doesn't exist on cartridge
                
                # Create directory in prefix if needed
                save_path.mkdir(parents=True, exist_ok=True)
                
                # Copy all files from this save location
                try:
                    for save_file in cartridge_save_path.rglob('*'):
                        if save_file.is_file():
                            # Preserve directory structure
                            rel_path = save_file.relative_to(cartridge_save_path)
                            dest_file = save_path / rel_path
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(save_file, dest_file)
                            total_files += 1
                except Exception as e:
                    print(f"  Warning: Failed to restore from {save_path_str}: {e}")
            
            if total_files > 0:
                print(f"  ✓ Restored {total_files} save file(s) from cartridge")
            else:
                print("  No saves found on cartridge to restore")
        except Exception as e:
            print(f"  Warning: Failed to sync saves from cartridge: {e}")
    
    def _sync_saves_to_cartridge(self, cartridge) -> None:
        """Sync save files from local prefix back to cartridge
        
        Args:
            cartridge: Cartridge instance
        """
        try:
            # Check if we have configured save paths
            if not cartridge.metadata.save_paths:
                print("  Warning: No save_paths configured in metadata.toml")
                return
            
            prefix_path = cartridge.metadata.get_prefix_path()
            savedata_dir = Path(cartridge.mount_path) / "savedata"
            savedata_dir.mkdir(parents=True, exist_ok=True)
            
            total_files = 0
            
            # Backup saves for each configured path
            for save_path_str in cartridge.metadata.save_paths:
                # Construct full path in prefix
                save_path = prefix_path / save_path_str
                
                if not save_path.exists():
                    continue  # Skip if this save location doesn't exist in prefix
                
                # Construct corresponding path in savedata (preserves directory structure)
                cartridge_save_path = savedata_dir / save_path_str
                cartridge_save_path.mkdir(parents=True, exist_ok=True)
                
                # Copy all files to cartridge
                try:
                    for save_file in save_path.rglob('*'):
                        if save_file.is_file():
                            # Preserve directory structure
                            rel_path = save_file.relative_to(save_path)
                            dest_file = cartridge_save_path / rel_path
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(save_file, dest_file)
                            total_files += 1
                except Exception as e:
                    print(f"  Warning: Failed to backup from {save_path_str}: {e}")
            
            if total_files > 0:
                print(f"  ✓ Backed up {total_files} save file(s) to cartridge")
            else:
                print("  No saves found in prefix to backup")
        except Exception as e:
            print(f"  Warning: Failed to sync saves to cartridge: {e}")
    
    def is_game_running(self, uuid: str) -> bool:
        """Check if a game is currently running
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            True if game is running, False otherwise
        """
        if uuid not in self.running_games:
            return False
        
        running_game = self.running_games[uuid]
        if not running_game.is_running():
            # Clean up finished game
            self._handle_game_stopped(uuid)
            return False
        
        return True
    
    def stop_game(self, uuid: str) -> bool:
        """Stop a running game
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            True if stopped successfully, False otherwise
        """
        if uuid not in self.running_games:
            return False
        
        try:
            running_game = self.running_games[uuid]
            print(f"Stopping game: {running_game.game_name}")
            running_game.terminate()
            self._handle_game_stopped(uuid)
            return True
        except Exception as e:
            print(f"Error stopping game {uuid}: {e}")
            return False
    
    def _handle_game_stopped(self, uuid: str):
        """Handle cleanup when a game stops
        
        Args:
            uuid: Cartridge UUID
        """
        if uuid not in self.running_games:
            return
        
        running_game = self.running_games[uuid]
        session_playtime = running_game.get_playtime()
        
        print(f"Game stopped: {running_game.game_name}")
        print(f"  Session playtime: {session_playtime // 60} minutes")
        
        # Update metadata
        cartridge = self.scanner.get_cartridge(uuid)
        if cartridge:
            try:
                cartridge.metadata.update_playtime(session_playtime)
                cartridge.save_metadata()
                print(f"  Total playtime: {cartridge.metadata.total_playtime // 3600}h {(cartridge.metadata.total_playtime % 3600) // 60}m")
                
                # Backup saves to cartridge
                print("  Syncing saves to cartridge...")
                self._sync_saves_to_cartridge(cartridge)
            except Exception as e:
                print(f"Error updating metadata: {e}")
        
        # Remove from running games
        del self.running_games[uuid]
        
        # Signal will be emitted by the service
    
    def check_running_games(self) -> list[str]:
        """Check all running games and clean up finished ones
        
        Returns:
            List of UUIDs for games that stopped
        """
        stopped_uuids = []
        
        for uuid in list(self.running_games.keys()):
            if not self.is_game_running(uuid):
                stopped_uuids.append(uuid)
        
        return stopped_uuids
    
    def get_running_games(self) -> list[Dict]:
        """Get list of currently running games
        
        Returns:
            List of running game info dictionaries
        """
        result = []
        for uuid, running_game in self.running_games.items():
            if running_game.is_running():
                result.append({
                    'uuid': uuid,
                    'game_name': running_game.game_name,
                    'pid': running_game.process.pid,
                    'playtime': running_game.get_playtime()
                })
        return result

