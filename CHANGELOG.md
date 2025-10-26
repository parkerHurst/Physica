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

## [1.0.1] - 2025-10-25

### Bug Fixes
- 🔧 **Fixed Debian/Ubuntu installation issues**
  - Resolved `metadata-generation-failed` error with `dbus-python`
  - Fixed `ModuleNotFoundError` for `gi` and `dbus` modules in virtual environment
  - Added automatic build dependency detection and installation
  - Updated installer to handle missing system packages gracefully

### Improvements
- 📚 **Enhanced documentation**
  - Added OS-specific installation prerequisites
  - Detailed troubleshooting guide for common installation issues
  - Clear error messages with solution commands

### Technical Changes
- 🛠️ **Updated installer logic**
  - Automatically detects missing build dependencies
  - Installs build tools via package manager when needed
  - Falls back to pip installation if system packages unavailable
  - Added comprehensive build dependency packages for Debian/Ubuntu

---

## [1.1.0] - 2025-10-26

### New Features
- 🎨 **Added Physica logo/icon** - Custom SVG icon integrated throughout the application
- 📦 **Improved packaging** - Icon included in all distribution methods

### Improvements
- 🔧 **Removed Flatpak support** - Simplified distribution as Flatpak sandboxing incompatible with system-level USB operations
- 🧹 **Code cleanup** - Removed deprecated Flatpak-specific code from import wizard
- 📝 **Updated all version references** - Bumped to v1.1 across all files

### Technical Changes
- Updated installation scripts to include icon
- Updated PKGBUILD to install icon
- Updated uninstaller to remove icon
- Updated package.sh to include icon in distribution

---

## Version History

### v1.1.0 (2025-10-26)
**New:** Added custom icon, removed Flatpak support

### v1.0.1 (2025-10-25)
**Fix:** Debian/Ubuntu installation issues - proper build dependencies and system package usage

### v1.0-EA-rev2 (2025-10-25)
**Fix:** Installer now uses virtual environment to avoid `externally-managed-environment` error on modern Python distributions (Arch Linux, etc.)

### v1.0-EA-rev1 (2025-10-25)
**Initial:** First public early access release

