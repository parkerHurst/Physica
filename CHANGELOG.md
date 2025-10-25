# Changelog

All notable changes to Physica will be documented in this file.

## [1.0-EA] - 2025-10-25

### Initial Early Access Release

#### Features
- 🎮 Physical game cartridge system for PC games
- 🔌 Plug-and-play auto-launch functionality
- 💾 Portable save file synchronization
- 🎨 Memory card manager UI (GTK4 + libadwaita)
- 📦 Import wizard with automatic USB formatting
- ⏱️ Playtime tracking and statistics
- 🔔 Toast notifications for cartridge events
- 🖱️ Context menu actions (launch, open location, remove)
- 🐧 Proton/Wine integration for Windows games

#### Installation
- Automated installer script (`install.sh`)
- Virtual environment isolation for dependencies
- Desktop integration with app menu entry
- Service autostart configuration
- Clean uninstaller (`uninstall.sh`)

#### Technical
- D-Bus service for inter-process communication
- Persistent game registry with play history
- USB drive monitoring and detection
- Automatic save synchronization
- Support for multiple Proton versions

#### Known Issues
- Some games may not work with Proton (check ProtonDB)
- Service requires manual start on first run (auto-starts after)
- No custom game icons yet (text-only cards)
- Emoji placeholders removed for stability

#### Tested Games
- ✅ Stardew Valley - Full compatibility

---

## Version History

### v1.0-EA-rev2 (2025-10-25)
**Fix:** Installer now uses virtual environment to avoid `externally-managed-environment` error on modern Python distributions (Arch Linux, etc.)

### v1.0-EA-rev1 (2025-10-25)
**Initial:** First public early access release

