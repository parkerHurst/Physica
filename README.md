# 🎮 Physica - Physical Game Cartridge Manager

**Turn your USB drives into physical game cartridges for PC games.**

Physica brings the nostalgic experience of physical game cartridges to modern PC gaming. Each cartridge is a self-contained, portable package with the game, saves, and Wine prefix—plug it in, play your game, unplug it, and take it anywhere.

---

## ✨ Features

- 🔌 **Plug-and-Play** - Insert cartridge, game auto-launches
- 💾 **Portable Saves** - Save files sync automatically to the cartridge
- ⏱️ **Playtime Tracking** - Track hours played per game
- 🎨 **Memory Card Manager UI** - Beautiful GTK4 interface inspired by classic console memory card managers
- 📦 **Self-Contained** - Each cartridge includes game files, saves, and Wine prefix
- 🚀 **Quick Launch** - Click-to-launch from the desktop app
- 🔔 **Toast Notifications** - Visual feedback for all cartridge events

---

## 🖼️ Screenshots

### Memory Card Manager UI
- View all games you've ever played (even when cartridge not inserted)
- Launch games with one click
- See playtime and last played date
- Right-click for quick actions (launch, open location, remove from library)

### Import Wizard
- Easy game import with automatic USB formatting
- Detects game executables and save locations
- Configures Proton automatically

---

## 📋 Requirements

- **OS:** Linux (tested on Omarchy)
- **Python:** 3.11+
- **Desktop:** GTK4 + libadwaita (for GUI)
- **Dependencies:** See `requirements.txt` files in each component

---

## 🚀 Quick Start

### Option A: Automated Installation (Recommended)

```bash
# 1. Clone or download
git clone https://github.com/parkerHurst/Physica.git
cd Physica

# 2. Run installer
./install.sh

# 3. Start service
physica-service

# 4. Launch GUI (in new terminal)
physica
```

The installer will:
- ✅ Check dependencies
- ✅ Install Python packages
- ✅ Create launchers in `~/.local/bin`
- ✅ Add desktop entry
- ✅ Configure autostart for the service

### Option B: Manual Development Setup

For development or if you prefer manual control:

```bash
# 1. Clone the repository
git clone https://github.com/parkerHurst/Physica.git
cd Physica

# 2. Install service dependencies
cd service
pip install --user -r requirements.txt
cd ..

# 3. Install GTK app dependencies
cd gtk-app
pip install --user -r requirements.txt
cd ..

# 4. Run the service
./run_service.sh

# 5. Launch the GTK app (in new terminal)
cd gtk-app
python3 run.py
```

Keep the service terminal open. The service will run in the foreground and show logs. In the future, this will run in the background.

---

## 📦 Creating Your First Game Cartridge

### Method 1: Using the Import Wizard (Recommended)

1. Launch the GTK app
2. Click the **"Format New Cartridge"** card
3. Follow the wizard:
   - Select your game directory
   - Select a USB drive
   - USB will be automatically formatted and prepared
   - Game files will be copied to the cartridge
4. Done! Your cartridge will appear in the library

### Method 2: Manual Setup

See [MANUAL_SETUP.md](docs/MANUAL_SETUP.md) for advanced cartridge creation.

---

## 🎮 Using Physica

### Auto-Launch Mode

1. Insert a game cartridge (USB drive with `.gamecard/` structure)
2. Wait 2 seconds
3. Game launches automatically!
4. Play your game
5. Exit the game - saves sync back to the cartridge
6. Eject the cartridge safely

### Manual Launch Mode

1. Insert a game cartridge
2. Open the GTK app
3. Click the **Launch** button on the game card
4. Play your game
5. Exit when done

### Context Menu Actions

Right-click any game card for:
- **Launch Game** - Start playing
- **View Details** - See game info (coming soon)
- **Open Cartridge Location** - Opens file manager
- **Remove from Library** - Delete from registry (cartridge files stay intact)

---

## 📁 Project Structure

```
Physica/
├── service/              # Background service (D-Bus daemon)
│   ├── main.py          # Service entry point
│   ├── cartridge.py     # Cartridge data structures
│   ├── cartridge_scanner.py   # USB monitoring
│   ├── game_launcher.py        # Proton/Wine integration
│   ├── cartridge_registry.py  # Persistent game database
│   └── dbus_service.py         # D-Bus interface
│
├── gtk-app/             # GTK4 Desktop application
│   ├── physica_gtk/
│   │   ├── main.py      # Application entry point
│   │   ├── window.py    # Main window (memory card UI)
│   │   ├── game_card.py # Game card widgets
│   │   ├── import_wizard.py  # Game import wizard
│   │   └── dbus_client.py    # D-Bus communication
│   └── run.py
│
├── scripts/             # Utility scripts
│   └── import_game.py   # CLI game import tool
│
├── install.sh           # Automated installer
├── uninstall.sh         # Uninstaller
├── package.sh           # Create distribution tarball
└── run_service.sh       # Service launcher (manual mode)
```

---

## 📦 Distribution

### For Developers

Create a distribution package:

```bash
./package.sh
```

This creates `build/physica-1.0-EA.tar.gz` ready for distribution.

See [DISTRIBUTION.md](DISTRIBUTION.md) for complete packaging and distribution guide.

### For End Users

Download the latest release from [GitHub Releases](https://github.com/parkerHurst/Physica/releases), extract, and run `./install.sh`.

---

## ⚙️ Configuration

Configuration file: `~/.config/physica/config.toml`

```toml
[service]
scan_interval = 5              # Seconds between USB scans
mount_base = "/media/deck"     # Base mount directory (auto-detects all)
auto_launch_delay = 2          # Seconds to wait before auto-launching

[wine]
default_version = "GE-Proton10-17"
search_paths = [
    "~/.steam/steam/steamapps/common",
    "~/.local/share/Steam/compatibilitytools.d"
]
```

---

## 🎯 Cartridge Structure

Each cartridge is a USB drive with this structure:

```
/media/username/CARTRIDGE_NAME/
├── .gamecard/
│   └── metadata.toml    # Game metadata and configuration
├── game/                # Game files
├── savedata/            # Synchronized save files (portable)
└── (Wine prefix stored locally on fast storage)
```

### Example `metadata.toml`:

```toml
[game]
name = "Stardew Valley"
id = "stardew_valley"
executable = "game/Stardew Valley.exe"

[runtime]
platform = "windows"
needs_wine = true
wine_version = "GE-Proton10-17"
launch_args = []
working_directory = "game"
save_paths = [
    "drive_c/users/steamuser/AppData/Roaming/StardewValley"
]

[cartridge]
uuid = "550e8400-e29b-41d4-a716-446655440000"
created_at = "2025-10-24T20:00:00"
original_size = 500000000
auto_launch = true

[stats]
total_playtime = 0
play_count = 0
last_played = ""
```

---

## 🔧 Troubleshooting

### Service Won't Start

```bash
# Check if D-Bus is available
dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames

# Run service with debug output
cd service
python3 -u main.py --debug
```

### Game Won't Launch

1. Check if Proton is installed: `ls ~/.steam/steam/steamapps/common/`
2. Verify cartridge structure: `ls -la /media/username/CARTRIDGE/.gamecard/`
3. Check service logs in the terminal where `run_service.sh` is running
4. Try launching manually: `python3 scripts/import_game.py --help`
5. Check [ProtonDB](https://protondb.com) for game incompatibility

### Saves Not Syncing

1. Check `save_paths` in `metadata.toml`
2. Verify Wine prefix location: `~/.local/share/physica/prefixes/`
3. Look for saves in: `savedata/` on the cartridge

---

## 🛠️ Development

### Running Tests

```bash
# Test D-Bus connection
cd gtk-app
python3 -c "from physica_gtk.dbus_client import PhysicaDBusClient; print(PhysicaDBusClient().is_connected())"

# Test game card rendering
python3 -c "from physica_gtk.game_card import GameCard; print('OK')"
```

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📜 License

MIT

---

## 🙏 Credits

- **Proton/Wine** - Windows compatibility layer
- **GTK4/libadwaita** - Modern Linux UI framework
- **D-Bus** - Inter-process communication

---

## 🗺️ Roadmap

### Phase 2.5: UI Polish (Optional)
- [ ] Custom game icons/cover art
- [ ] Loading spinners during launch
- [ ] Better animations
- [ ] Game details dialog

### Phase 3: Decky Plugin
- [ ] Steam Deck Gaming Mode integration
- [ ] Quick access overlay
- [ ] Per-game settings

### Phase 4: Advanced Features
- [ ] Cloud save backup
- [ ] Multi-cartridge support (USB hubs)
- [ ] Cartridge health monitoring
- [ ] Play session statistics

---

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/parkerHurst/Physica/issues)
- **Discussions:** [GitHub Discussions](https://github.com/parkerHurst/Physica/discussions)

---

**Made with ❤️ for the Steam Deck and Linux gaming community**
