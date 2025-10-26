#!/usr/bin/env python3
"""
Automatic game importer for Physica
Detects executables, save paths, and creates proper cartridge structure

Usage:
    ./import_game.py <game_directory> <usb_mount_point>
    
Example:
    ./import_game.py ~/Games/Celeste /media/deck/CELESTE
"""

import sys
import os
import subprocess
import toml
from pathlib import Path
from datetime import datetime
import uuid as uuid_lib

class GameImporter:
    """Automatic game importer"""
    
    def __init__(self, game_dir: Path, cartridge_mount: Path):
        """Initialize importer
        
        Args:
            game_dir: Source game directory
            cartridge_mount: Target USB mount point
        """
        self.game_dir = Path(game_dir).resolve()
        self.cartridge_mount = Path(cartridge_mount).resolve()
        
        if not self.game_dir.exists():
            raise ValueError(f"Game directory not found: {game_dir}")
        
        if not self.cartridge_mount.exists():
            raise ValueError(f"Cartridge mount point not found: {cartridge_mount}")
    
    def find_executables(self) -> list[Path]:
        """Find all .exe files in game directory
        
        Returns:
            List of .exe file paths relative to game directory
        """
        exe_files = []
        for exe_path in self.game_dir.rglob("*.exe"):
            # Skip common non-game executables
            name = exe_path.name.lower()
            if any(skip in name for skip in ['unins', 'crash', 'report', 'update', 'setup', 'redist', 'vcredist', 'directx', 'easyanticheat', 'battleye']):
                continue
            exe_files.append(exe_path.relative_to(self.game_dir))
        return exe_files
    
    def guess_main_executable(self, executables: list[Path]) -> Path:
        """Guess which executable is the main game
        
        Args:
            executables: List of executable paths
            
        Returns:
            Most likely main executable
        """
        if not executables:
            raise ValueError("No executables found in game directory")
        
        if len(executables) == 1:
            return executables[0]
        
        # Scoring system to guess the main exe
        scores = {}
        game_name = self.game_dir.name.lower()
        
        for exe in executables:
            score = 0
            name = exe.stem.lower()
            
            # Prefer executables in root or direct subdirectory
            if len(exe.parts) <= 2:
                score += 10
            
            # Prefer executables with game name in them
            if game_name in name or name in game_name:
                score += 20
            
            # Prefer shorter names (usually the main exe)
            score -= len(name)
            
            # Bonus for being named "game" or similar
            if name in ['game', 'main', 'start', 'launch']:
                score += 5
            
            # Penalty for launcher-like names
            if 'launcher' in name or 'config' in name:
                score -= 20
            
            scores[exe] = score
        
        # Return highest scored executable
        return max(scores, key=scores.get)
    
    def detect_save_location(self) -> list[str]:
        """Detect where the game saves data
        
        Returns:
            List of save_paths for metadata.toml
        """
        # Check if game saves to its own directory
        # Common save folder names
        save_dirs = ['Saves', 'SaveData', 'Save', 'Savegames', 'saves', 'savedata']
        for save_dir in save_dirs:
            if (self.game_dir / save_dir).exists():
                print(f"  ✓ Detected in-game save directory: {save_dir}/")
                return []  # No need for save_paths - saves are with game files
        
        # Otherwise, assume AppData (most common for Windows games)
        game_id = self.game_dir.name
        save_paths = [
            f"drive_c/users/steamuser/AppData/Local/{game_id}",
            f"drive_c/users/steamuser/AppData/LocalLow/{game_id}",
            f"drive_c/users/steamuser/AppData/Roaming/{game_id}",
        ]
        
        print(f"  ⚠ Save location unknown - will monitor AppData")
        print(f"    (You may need to adjust save_paths in metadata.toml)")
        return save_paths
    
    def get_game_size(self) -> int:
        """Calculate total size of game directory
        
        Returns:
            Size in bytes
        """
        total = 0
        for path in self.game_dir.rglob('*'):
            if path.is_file():
                total += path.stat().st_size
        return total
    
    def create_metadata(self, main_exe: Path, save_paths: list[str]) -> dict:
        """Generate metadata.toml content
        
        Args:
            main_exe: Path to main executable (relative to game dir)
            save_paths: List of save paths
            
        Returns:
            Metadata dictionary
        """
        game_name = self.game_dir.name
        game_id = game_name.lower().replace(' ', '_').replace('-', '_')
        cartridge_uuid = str(uuid_lib.uuid4())
        
        # Make executable path relative to game/ subdirectory on cartridge
        exe_path = f"game/{main_exe}"
        
        metadata = {
            "game": {
                "name": game_name,
                "id": game_id,
                "version": "1.1.1",
                "publisher": "",
                "release_date": "",
                "executable": exe_path,
                "genre": []
            },
            "runtime": {
                "platform": "windows",
                "needs_wine": True,
                "wine_version": "GE-Proton10-17",
                "launch_args": [],
                "working_directory": "game",
                "save_paths": save_paths
            },
            "cartridge": {
                "formatted_date": datetime.now().strftime("%Y-%m-%d"),
                "uuid": cartridge_uuid,
                "total_playtime": 0,
                "last_played": "",
                "play_count": 0,
                "notes": f"Auto-imported by Physica on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "auto_launch": True  # Default: auto-launch enabled
            },
            "import": {
                "source": "directory",
                "import_date": datetime.now().isoformat(),
                "original_size": self.get_game_size(),
                "source_path": str(self.game_dir)
            }
        }
        
        return metadata
    
    def import_game(self) -> tuple[bool, str]:
        """Run the complete import process
        
        Returns:
            (success, uuid/error_message)
        """
        print(f"🎮 Physica Game Importer")
        print(f"=======================\n")
        print(f"Source: {self.game_dir}")
        print(f"Target: {self.cartridge_mount}\n")
        
        # Step 1: Detect executables
        print("Step 1: Detecting game executables...")
        executables = self.find_executables()
        if not executables:
            return False, "No executable files found in game directory"
        
        print(f"  Found {len(executables)} executable(s):")
        for exe in executables:
            print(f"    - {exe}")
        
        main_exe = self.guess_main_executable(executables)
        print(f"  ✓ Selected main executable: {main_exe}\n")
        
        # Step 2: Detect save location
        print("Step 2: Detecting save location...")
        save_paths = self.detect_save_location()
        print()
        
        # Step 3: Create cartridge structure
        print("Step 3: Creating cartridge structure...")
        try:
            gamecard_dir = self.cartridge_mount / ".gamecard"
            game_dir = self.cartridge_mount / "game"
            savedata_dir = self.cartridge_mount / "savedata"
            
            gamecard_dir.mkdir(parents=True, exist_ok=True)
            game_dir.mkdir(parents=True, exist_ok=True)
            savedata_dir.mkdir(parents=True, exist_ok=True)
            print("  ✓ Directories created\n")
        except Exception as e:
            return False, f"Failed to create cartridge structure: {e}"
        
        # Step 4: Generate metadata
        print("Step 4: Generating metadata...")
        metadata = self.create_metadata(main_exe, save_paths)
        metadata_path = gamecard_dir / "metadata.toml"
        
        try:
            with open(metadata_path, 'w') as f:
                toml.dump(metadata, f)
            print(f"  ✓ Metadata written to {metadata_path}\n")
        except Exception as e:
            return False, f"Failed to write metadata: {e}"
        
        # Step 5: Copy game files
        print("Step 5: Copying game files...")
        print(f"  Source size: {metadata['import']['original_size'] / 1024**3:.2f} GB")
        print(f"  This may take a few minutes...")
        
        try:
            # Use rsync for efficient copying with progress
            cmd = [
                'rsync', '-ah', '--info=progress2',
                f"{self.game_dir}/",
                f"{game_dir}/"
            ]
            subprocess.run(cmd, check=True)
            print("  ✓ Game files copied\n")
        except subprocess.CalledProcessError as e:
            return False, f"Failed to copy game files: {e}"
        except FileNotFoundError:
            # rsync not available, fall back to cp
            try:
                subprocess.run(['cp', '-r', f"{self.game_dir}/.", str(game_dir)], check=True)
                print("  ✓ Game files copied\n")
            except subprocess.CalledProcessError as e:
                return False, f"Failed to copy game files: {e}"
        
        # Success!
        print("=" * 50)
        print("✅ Import Complete!")
        print("=" * 50)
        print(f"\nCartridge Details:")
        print(f"  Name: {metadata['game']['name']}")
        print(f"  UUID: {metadata['cartridge']['uuid']}")
        print(f"  Executable: {metadata['game']['executable']}")
        print(f"  Location: {self.cartridge_mount}")
        print(f"\nThe cartridge is ready to use!")
        print(f"Insert it and launch the game via Physica.")
        
        return True, metadata['cartridge']['uuid']


def main():
    """Main entry point"""
    if len(sys.argv) != 3:
        print("Usage: import_game.py <game_directory> <usb_mount_point>")
        print("\nExample:")
        print("  ./import_game.py ~/Games/Celeste /media/deck/CELESTE")
        sys.exit(1)
    
    game_dir = Path(sys.argv[1])
    cartridge_mount = Path(sys.argv[2])
    
    try:
        importer = GameImporter(game_dir, cartridge_mount)
        success, result = importer.import_game()
        
        if success:
            sys.exit(0)
        else:
            print(f"\n❌ Import failed: {result}", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

