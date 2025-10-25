"""Cartridge detection and scanning"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    from .cartridge import Cartridge, CartridgeMetadata
    from .config import Config
except ImportError:
    from cartridge import Cartridge, CartridgeMetadata
    from config import Config


class CartridgeScanner:
    """Scans for and manages game cartridges"""
    
    def __init__(self, config: Config):
        """Initialize scanner
        
        Args:
            config: Service configuration
        """
        self.config = config
        self.cartridges: Dict[str, Cartridge] = {}  # uuid -> Cartridge
        self._last_scan_uuids: Set[str] = set()
    
    def _get_all_mount_points(self) -> List[Path]:
        """Get all mount points on the system
        
        Returns:
            List of mount point paths
        """
        mount_points = []
        
        try:
            result = subprocess.run(
                ['lsblk', '-J', '-o', 'MOUNTPOINT,TYPE'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                for device in data.get('blockdevices', []):
                    # Check disk-level mountpoint
                    mountpoint = device.get('mountpoint')
                    if mountpoint and mountpoint not in ['/', '[SWAP]']:
                        mount_points.append(Path(mountpoint))
                    
                    # Check partition mountpoints
                    for child in device.get('children', []):
                        mountpoint = child.get('mountpoint')
                        if mountpoint and mountpoint not in ['/', '[SWAP]']:
                            mount_points.append(Path(mountpoint))
        
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not get mount points from lsblk: {e}")
        
        return mount_points
    
    def scan_for_cartridges(self) -> List[Cartridge]:
        """Scan all mounted drives for game cartridges
        
        This method checks:
        1. All mount points found via lsblk (auto-discovery)
        2. Subdirectories in the configured mount_base (legacy support)
        
        Returns:
            List of detected cartridges
        """
        detected_cartridges = []
        checked_paths = set()
        
        # Method 1: Auto-discover cartridges on any mounted drive
        mount_points = self._get_all_mount_points()
        
        for mount_point in mount_points:
            if mount_point in checked_paths:
                continue
            checked_paths.add(mount_point)
            
            # Check if this mount point itself is a cartridge
            try:
                cartridge = Cartridge.from_mount_path(mount_point)
                if cartridge and cartridge.is_valid():
                    detected_cartridges.append(cartridge)
                    print(f"Found cartridge: {cartridge.metadata.game_name} at {mount_point} (UUID: {cartridge.metadata.uuid})")
            except Exception as e:
                # Not a cartridge, that's fine
                pass
        
        # Method 2: Check configured mount_base for subdirectories (legacy support)
        mount_base = Path(self.config.mount_base)
        
        if mount_base.exists():
            try:
                for entry in mount_base.iterdir():
                    if entry.is_dir() and entry not in checked_paths:
                        checked_paths.add(entry)
                        cartridge = Cartridge.from_mount_path(entry)
                        if cartridge and cartridge.is_valid():
                            detected_cartridges.append(cartridge)
                            print(f"Found cartridge: {cartridge.metadata.game_name} at {entry} (UUID: {cartridge.metadata.uuid})")
            except Exception as e:
                print(f"Warning: Error scanning mount_base {mount_base}: {e}")
        
        return detected_cartridges
    
    def refresh_cartridges(self) -> tuple[List[str], List[str]]:
        """Refresh cartridge registry by scanning filesystem
        
        Returns:
            Tuple of (inserted_uuids, removed_uuids)
        """
        detected = self.scan_for_cartridges()
        current_uuids = {c.metadata.uuid for c in detected}
        
        # Determine what was inserted and removed
        inserted_uuids = current_uuids - self._last_scan_uuids
        removed_uuids = self._last_scan_uuids - current_uuids
        
        # Update registry
        # Remove cartridges that are no longer present
        for uuid in removed_uuids:
            if uuid in self.cartridges:
                cartridge = self.cartridges[uuid]
                cartridge.metadata.is_mounted = False
                print(f"Cartridge removed: {cartridge.metadata.game_name} (UUID: {uuid})")
                del self.cartridges[uuid]
        
        # Add or update cartridges that are present
        for cartridge in detected:
            uuid = cartridge.metadata.uuid
            if uuid in inserted_uuids:
                print(f"Cartridge inserted: {cartridge.metadata.game_name} (UUID: {uuid})")
            self.cartridges[uuid] = cartridge
        
        self._last_scan_uuids = current_uuids
        
        return list(inserted_uuids), list(removed_uuids)
    
    def get_cartridge(self, uuid: str) -> Optional[Cartridge]:
        """Get cartridge by UUID
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            Cartridge instance or None if not found
        """
        return self.cartridges.get(uuid)
    
    def list_cartridges(self) -> List[Cartridge]:
        """Get list of all mounted cartridges
        
        Returns:
            List of all cartridges in registry
        """
        return list(self.cartridges.values())
    
    def get_cartridge_info(self, uuid: str) -> Optional[Dict]:
        """Get cartridge information as dictionary
        
        Args:
            uuid: Cartridge UUID
            
        Returns:
            Dictionary with cartridge info or None
        """
        cartridge = self.get_cartridge(uuid)
        if cartridge:
            return cartridge.metadata.to_dict()
        return None
    
    def list_cartridges_info(self) -> List[Dict]:
        """Get all cartridges as list of dictionaries
        
        Returns:
            List of cartridge info dictionaries
        """
        return [c.metadata.to_dict() for c in self.cartridges.values()]


def main():
    """Standalone test for cartridge scanner"""
    import sys
    
    print("=== Physica Cartridge Scanner Test ===\n")
    
    # Create config
    config = Config()
    print(f"Scanning mount base: {config.mount_base}")
    print(f"Scan interval: {config.scan_interval} seconds")
    print(f"Config directory: {config.config_dir}")
    print(f"Cache directory: {config.cache_dir}\n")
    
    # Create scanner
    scanner = CartridgeScanner(config)
    
    # Initial scan
    print("Performing initial scan...\n")
    inserted, removed = scanner.refresh_cartridges()
    
    # Display results
    cartridges = scanner.list_cartridges()
    
    if not cartridges:
        print("No cartridges detected.")
        print(f"\nTo test, create a cartridge structure at {config.mount_base}/TEST_GAME/")
        print("with .gamecard/metadata.toml file")
        return
    
    print(f"Found {len(cartridges)} cartridge(s):\n")
    
    for cartridge in cartridges:
        meta = cartridge.metadata
        print(f"📀 {meta.game_name}")
        print(f"   UUID: {meta.uuid}")
        print(f"   Publisher: {meta.publisher}")
        print(f"   Version: {meta.version}")
        print(f"   Platform: {meta.platform}")
        print(f"   Wine Version: {meta.wine_version}")
        print(f"   Executable: {meta.executable}")
        print(f"   Mount Path: {meta.mount_path}")
        print(f"   Playtime: {meta.total_playtime // 3600}h {(meta.total_playtime % 3600) // 60}m")
        print(f"   Play Count: {meta.play_count}")
        
        if meta.last_played:
            print(f"   Last Played: {meta.last_played}")
        
        print()
    
    # Test individual lookup
    if cartridges:
        test_uuid = cartridges[0].metadata.uuid
        print(f"\nTesting GetCartridge for UUID: {test_uuid}")
        info = scanner.get_cartridge_info(test_uuid)
        if info:
            print(f"✓ Successfully retrieved: {info['game_name']}")
        else:
            print("✗ Failed to retrieve cartridge")


if __name__ == "__main__":
    main()

