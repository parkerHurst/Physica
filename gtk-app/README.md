# Physica GTK4 Desktop Application

Modern desktop interface for managing Physica game cartridges.

## Requirements

- Python 3.11+
- GTK4
- libadwaita
- PyGObject

### Install System Dependencies (Arch Linux)

```bash
sudo pacman -S gtk4 libadwaita python-gobject
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Running

```bash
./run.py
```

Or from the project root:

```bash
cd gtk-app && ./run.py
```

## Development Status

**Phase 2.0 - Step 1: ✅ Complete**
- [x] Basic window with GTK4
- [x] libadwaita styling
- [x] Header bar with refresh button
- [x] Cartridge grid layout (FlowBox)
- [x] Test cartridge cards
- [x] Empty state
- [x] Custom CSS styling
- [x] Keyboard shortcuts (Ctrl+Q, Ctrl+R)

**Phase 2.0 - Step 2: 🚧 Next**
- [ ] D-Bus client wrapper
- [ ] Connect to Physica service
- [ ] Load real cartridge data

## Project Structure

```
gtk-app/
├── physica_gtk/
│   ├── __init__.py           # Package metadata
│   ├── main.py               # Application class, CSS loading
│   ├── window.py             # Main window and UI
│   ├── style.css             # Custom styling
│   ├── cartridge_card.py     # TODO: Cartridge card widget
│   ├── dbus_client.py        # TODO: D-Bus communication
│   └── utils.py              # TODO: Helper functions
├── run.py                    # Launcher script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Features

### Current (Step 1)
- Modern libadwaita window
- Responsive grid layout
- Test cartridge cards with:
  - Cover art placeholder
  - Game name
  - Playtime display
  - Last played date
  - Launch button
- Empty state when no cartridges
- Keyboard shortcuts

### Coming Soon (Steps 2-6)
- Real D-Bus integration
- Dynamic cartridge loading
- Launch games from UI
- Live status updates
- Signal listeners for cartridge insert/remove
- Running game indicators

## Design

- **Layout:** Grid (like Steam library)
- **Cards:** 280px wide, adaptive height
- **Spacing:** 24px between cards
- **Theme:** libadwaita adaptive (light/dark)
- **Touch:** Large buttons for Steam Deck

## Testing

1. Make sure Physica service is running:
   ```bash
   cd ~/Projects/Physica
   ./run_service.sh
   ```

2. Launch the GTK app:
   ```bash
   cd ~/Projects/Physica/gtk-app
   ./run.py
   ```

3. You should see:
   - Window with "Physica" title
   - Refresh button in header
   - Grid with 3 test cartridge cards
   - Nice hover effects on cards
   - Launch buttons that print to console

## Keyboard Shortcuts

- `Ctrl+Q` - Quit application
- `Ctrl+R` or `F5` - Refresh cartridges

## TODO

- [ ] D-Bus client implementation
- [ ] Real cartridge data loading
- [ ] Launch button integration
- [ ] Status indicators (running games)
- [ ] Signal listeners
- [ ] Cover art support
- [ ] Details view
- [ ] Settings panel
