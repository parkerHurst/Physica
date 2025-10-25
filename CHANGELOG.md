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

## [1.0.1-EA] - 2025-10-25

### Bug Fixes
- 🔧 **Fixed Debian/Ubuntu installation issues**
  - Resolved `metadata-generation-failed` error with `dbus-python`
  - Added proper build dependency checks (`pkg-config`, `cmake`, `dbus-1`)
  - Updated installer to use system packages for problematic dependencies
  - Added comprehensive troubleshooting section to README

### Improvements
- 📚 **Enhanced documentation**
  - Added OS-specific installation prerequisites
  - Detailed troubleshooting guide for common installation issues
  - Clear error messages with solution commands

### Technical Changes
- 🛠️ **Updated requirements.txt**
  - Removed `dbus-python` and `PyGObject` from pip requirements
  - Now uses system packages (`python3-dbus`, `python3-gi`) to avoid build issues
  - Added comments explaining system package dependencies

---

## Version History

### v1.0.1-EA (2025-10-25)
**Fix:** Debian/Ubuntu installation issues - proper build dependencies and system package usage

### v1.0-EA-rev2 (2025-10-25)
**Fix:** Installer now uses virtual environment to avoid `externally-managed-environment` error on modern Python distributions (Arch Linux, etc.)

### v1.0-EA-rev1 (2025-10-25)
**Initial:** First public early access release

