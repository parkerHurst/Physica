"""Cartridge data model and metadata handling"""

import toml
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CartridgeMetadata:
    """Represents a game cartridge's metadata"""
    
    # Game info
    game_name: str
    game_id: str
    version: str
    publisher: str = ""
    release_date: str = ""
    executable: str = ""
    genre: str = ""
    
    # Runtime info
    platform: str = "windows"
    needs_wine: bool = True
    wine_version: str = "GE-Proton8-14"
    launch_args: list = None
    working_directory: str = "game"
    save_paths: list = None  # List of paths to save directories relative to prefix
    env_vars: dict = None  # Custom environment variables for game launch
    
    # Cartridge info
    formatted_date: str = ""
    uuid: str = ""
    total_playtime: int = 0  # seconds
    last_played: str = ""
    play_count: int = 0
    notes: str = ""
    auto_launch: bool = True  # Auto-launch game when cartridge is inserted
    
    # Import info
    source: str = "directory"
    import_date: str = ""
    original_size: int = 0
    source_path: str = ""
    
    # Runtime-only (not in metadata.toml)
    mount_path: str = ""
    is_mounted: bool = False
    
    def __post_init__(self):
        if self.launch_args is None:
            self.launch_args = []
        if self.save_paths is None:
            self.save_paths = []
        if self.env_vars is None:
            self.env_vars = {}
    
    @classmethod
    def from_toml_file(cls, toml_path: Path, mount_path: str = "") -> 'CartridgeMetadata':
        """Load metadata from a TOML file
        
        Args:
            toml_path: Path to metadata.toml file
            mount_path: Path where the cartridge is mounted
            
        Returns:
            CartridgeMetadata instance
        """
        with open(toml_path, 'r') as f:
            data = toml.load(f)
        
        return cls(
            # Game section
            game_name=data.get("game", {}).get("name", "Unknown Game"),
            game_id=data.get("game", {}).get("id", ""),
            version=data.get("game", {}).get("version", ""),
            publisher=data.get("game", {}).get("publisher", ""),
            release_date=data.get("game", {}).get("release_date", ""),
            executable=data.get("game", {}).get("executable", ""),
            genre=data.get("game", {}).get("genre", ""),
            
            # Runtime section
            platform=data.get("runtime", {}).get("platform", "windows"),
            needs_wine=data.get("runtime", {}).get("needs_wine", True),
            wine_version=data.get("runtime", {}).get("wine_version", "GE-Proton8-14"),
            launch_args=data.get("runtime", {}).get("launch_args", []),
            working_directory=data.get("runtime", {}).get("working_directory", "game"),
            save_paths=data.get("runtime", {}).get("save_paths", []),
            env_vars=data.get("runtime", {}).get("env_vars", {}),
            
            # Cartridge section
            formatted_date=data.get("cartridge", {}).get("formatted_date", ""),
            uuid=data.get("cartridge", {}).get("uuid", ""),
            total_playtime=data.get("cartridge", {}).get("total_playtime", 0),
            last_played=data.get("cartridge", {}).get("last_played", ""),
            play_count=data.get("cartridge", {}).get("play_count", 0),
            notes=data.get("cartridge", {}).get("notes", ""),
            auto_launch=data.get("cartridge", {}).get("auto_launch", True),  # Default: enabled
            
            # Import section
            source=data.get("import", {}).get("source", "directory"),
            import_date=data.get("import", {}).get("import_date", ""),
            original_size=data.get("import", {}).get("original_size", 0),
            source_path=data.get("import", {}).get("source_path", ""),
            
            # Runtime-only
            mount_path=mount_path,
            is_mounted=True
        )
    
    def to_toml_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for TOML serialization
        
        Returns:
            Dictionary organized by sections
        """
        return {
            "game": {
                "name": self.game_name,
                "id": self.game_id,
                "version": self.version,
                "publisher": self.publisher,
                "release_date": self.release_date,
                "executable": self.executable,
                "genre": self.genre
            },
            "runtime": {
                "platform": self.platform,
                "needs_wine": self.needs_wine,
                "wine_version": self.wine_version,
                "launch_args": self.launch_args,
                "working_directory": self.working_directory,
                "save_paths": self.save_paths,
                "env_vars": self.env_vars
            },
            "cartridge": {
                "formatted_date": self.formatted_date,
                "uuid": self.uuid,
                "total_playtime": self.total_playtime,
                "last_played": self.last_played,
                "play_count": self.play_count,
                "notes": self.notes,
                "auto_launch": self.auto_launch
            },
            "import": {
                "source": self.source,
                "import_date": self.import_date,
                "original_size": self.original_size,
                "source_path": self.source_path
            }
        }
    
    def save_to_file(self, toml_path: Path):
        """Save metadata to a TOML file
        
        Args:
            toml_path: Path where to save metadata.toml
        """
        with open(toml_path, 'w') as f:
            toml.dump(self.to_toml_dict(), f)
    
    def update_playtime(self, session_seconds: int):
        """Update playtime statistics
        
        Args:
            session_seconds: Seconds played in this session
        """
        self.total_playtime += session_seconds
        self.last_played = datetime.now().isoformat()
        self.play_count += 1
    
    def get_executable_path(self) -> Path:
        """Get full path to game executable
        
        Returns:
            Full path to executable on cartridge
        """
        if not self.mount_path:
            raise ValueError("Cartridge not mounted")
        return Path(self.mount_path) / self.executable
    
    def get_prefix_path(self) -> Path:
        """Get full path to Wine prefix
        
        Returns:
            Full path to prefix directory (stored locally for performance)
        """
        if not self.mount_path:
            raise ValueError("Cartridge not mounted")
        # Store prefixes locally on fast storage, not on slow USB cartridges
        # Use game_id as the prefix directory name for uniqueness
        prefix_base = Path.home() / ".local/share/physica/prefixes"
        prefix_base.mkdir(parents=True, exist_ok=True)
        return prefix_base / self.game_id
    
    def get_working_directory_path(self) -> Path:
        """Get full path to working directory for game launch
        
        Returns:
            Full path to working directory
        """
        if not self.mount_path:
            raise ValueError("Cartridge not mounted")
        return Path(self.mount_path) / self.working_directory
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary for D-Bus transmission
        
        Returns:
            Flat dictionary with all metadata
        """
        return asdict(self)


class Cartridge:
    """Represents a physical game cartridge"""
    
    def __init__(self, mount_path: Path, metadata: CartridgeMetadata):
        """Initialize cartridge
        
        Args:
            mount_path: Path where cartridge is mounted
            metadata: Cartridge metadata
        """
        self.mount_path = mount_path
        self.metadata = metadata
        self.metadata.mount_path = str(mount_path)
        self.metadata.is_mounted = True
    
    @classmethod
    def from_mount_path(cls, mount_path: Path) -> Optional['Cartridge']:
        """Create Cartridge instance from a mount path by scanning for .gamecard/
        
        Args:
            mount_path: Path to check for cartridge
            
        Returns:
            Cartridge instance if valid, None otherwise
        """
        gamecard_dir = mount_path / ".gamecard"
        metadata_file = gamecard_dir / "metadata.toml"
        
        if not gamecard_dir.exists() or not metadata_file.exists():
            return None
        
        try:
            metadata = CartridgeMetadata.from_toml_file(metadata_file, str(mount_path))
            return cls(mount_path, metadata)
        except Exception as e:
            print(f"Error loading cartridge from {mount_path}: {e}")
            return None
    
    def is_valid(self) -> bool:
        """Check if cartridge has required files and valid metadata
        
        Returns:
            True if cartridge is valid
        """
        # Check for required directories
        required_dirs = [".gamecard", "game"]
        for dir_name in required_dirs:
            if not (self.mount_path / dir_name).exists():
                return False
        
        # Check for metadata
        if not self.metadata.uuid or not self.metadata.game_name:
            return False
        
        return True
    
    def save_metadata(self):
        """Save metadata back to cartridge"""
        metadata_file = self.mount_path / ".gamecard" / "metadata.toml"
        self.metadata.save_to_file(metadata_file)
    
    def __repr__(self) -> str:
        return f"Cartridge({self.metadata.game_name}, uuid={self.metadata.uuid}, mounted={self.mount_path})"

