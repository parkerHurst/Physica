# Contributing to Physica

Thank you for your interest in contributing to Physica! 🎮

## 🚀 Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/parkerHurst/Physica.git
cd Physica
```

### 2. Set Up Development Environment

```bash
python3 -m venv venv
source venv/bin/activate

# Install service dependencies
cd service
pip install -r requirements.txt
cd ..

# Install GTK app dependencies
cd gtk-app
pip install -r requirements.txt
cd ..
```

### 3. Run the Service

```bash
./run_service.sh
```

### 4. Run the GTK App

```bash
cd gtk-app
python3 run.py
```

---

## 📋 Development Guidelines

### Code Style

- **Python:** Follow PEP 8
- **Comments:** Use docstrings for all functions/classes
- **Type Hints:** Use type hints where applicable

### Git Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Test thoroughly
4. Commit with clear messages: `git commit -m "Add feature X"`
5. Push to your fork: `git push origin feature/your-feature-name`
6. Open a Pull Request

### Commit Messages

Format: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
- `feat: Add custom icon support for game cards`
- `fix: Launch button not resetting after game exit`
- `docs: Update installation instructions`

---

## 🧪 Testing

Before submitting a PR, please test:

1. **Service starts correctly:**
   ```bash
   ./run_service.sh
   ```

2. **GTK app launches:**
   ```bash
   cd gtk-app && python3 run.py
   ```

3. **Import wizard works:**
   - Click "Format New Cartridge"
   - Complete the wizard
   - Verify game appears in library

4. **Game launching works:**
   - Click Launch button
   - Game starts successfully
   - Exit game, button reappears

---

## 🐛 Reporting Bugs

When reporting bugs, please include:

- **OS and version** (e.g., Steam Deck, Arch Linux, Ubuntu 22.04)
- **Python version** (`python3 --version`)
- **Steps to reproduce** the bug
- **Expected behavior** vs **actual behavior**
- **Log output** (from service terminal)
- **Screenshots** (if UI-related)

---

## 💡 Feature Requests

We welcome feature ideas! Please:

1. Check existing issues first
2. Open a new issue with the `enhancement` label
3. Describe:
   - **Problem:** What issue does this solve?
   - **Solution:** How would it work?
   - **Alternatives:** Other approaches considered?
   - **Use case:** Real-world scenario?

---

## 📁 Project Structure

```
Physica/
├── service/              # Background service
│   ├── main.py          # Service entry point
│   ├── cartridge.py     # Data structures
│   ├── cartridge_scanner.py  # USB monitoring
│   ├── game_launcher.py      # Proton integration
│   ├── cartridge_registry.py # Game database
│   └── dbus_service.py       # D-Bus interface
│
├── gtk-app/             # GTK4 Desktop app
│   └── physica_gtk/
│       ├── main.py      # App entry point
│       ├── window.py    # Main window
│       ├── game_card.py # Card widgets
│       ├── import_wizard.py  # Import wizard
│       └── dbus_client.py    # D-Bus client
│
└── scripts/             # Utility scripts
```

---

## 🎯 Areas for Contribution

### High Priority
- [ ] **Game compatibility testing** - Test with more games
- [ ] **Icon/cover art support** - Add custom game icons
- [ ] **Details dialog** - Show full game metadata
- [ ] **Better error handling** - Improve error messages

### Medium Priority
- [ ] **Loading animations** - Add spinners during launch
- [ ] **Sorting/filtering** - Sort games by name, playtime, etc.
- [ ] **Statistics view** - Show play history graphs
- [ ] **Multi-platform support** - Test on other Linux distros

### Low Priority
- [ ] **Cloud save backup** - Optional backup to cloud storage
- [ ] **Multi-cartridge** - Support multiple USBs simultaneously
- [ ] **Themes** - Custom UI themes

---

## 🔧 Technical Notes

### D-Bus Interface

The service exposes these methods via D-Bus:

- `ListCartridges()` - Get all inserted cartridges
- `GetAllGames()` - Get all games from registry
- `LaunchGame(uuid)` - Launch a game
- `RefreshCartridges()` - Force cartridge rescan
- `RemoveFromRegistry(uuid)` - Remove game from library

Signals:
- `CartridgeInserted(uuid, name)` - Cartridge plugged in
- `CartridgeRemoved(uuid)` - Cartridge unplugged
- `GameLaunched(uuid, name)` - Game started
- `GameStopped(uuid, name, playtime)` - Game exited

### Save Synchronization

Saves sync bidirectionally:
- **On launch:** Copy from `cartridge/savedata/` → local prefix
- **On exit:** Copy from local prefix → `cartridge/savedata/`

This keeps saves portable while using fast local storage during gameplay.

### Wine Prefix Management

Prefixes are stored locally (`~/.local/share/physica/prefixes/`) for performance, not on the USB drive.

---

## 📚 Resources

- **GTK4 Documentation:** https://docs.gtk.org/gtk4/
- **Libadwaita:** https://gnome.pages.gitlab.gnome.org/libadwaita/
- **D-Bus Tutorial:** https://dbus.freedesktop.org/doc/dbus-tutorial.html
- **Proton Wiki:** https://github.com/ValveSoftware/Proton/wiki

---

## 🙏 Thank You!

Every contribution helps make Physica better for the community. Whether it's:
- Reporting bugs
- Suggesting features
- Improving documentation
- Writing code
- Testing games

**Your help is appreciated!** 🚀

---

## ❓ Questions?

- Open a [GitHub Discussion](https://github.com/parkerHurst/Physica/discussions)
- Check existing [Issues](https://github.com/parkerHurst/Physica/issues)
- Read the [README](README.md)

Happy coding! 🎮✨

