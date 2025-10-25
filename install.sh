#!/bin/bash
# Physica Installation Script
# For Linux systems with Python 3.11+

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║            Physica Installation Script v1.0.2              ║"
echo "║         Physical Game Cartridge Manager for Linux          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}✗ Please do NOT run this script as root${NC}"
    echo "  Run as your normal user. Sudo will be requested when needed."
    exit 1
fi

echo -e "${YELLOW}➜ Checking prerequisites...${NC}"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "  Please install Python 3.11 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check for GTK4 and dependencies
if ! python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null; then
    echo -e "${RED}✗ GTK4 not found${NC}"
    echo ""
    echo "Please install GTK4 dependencies:"
    echo "  Arch/Manjaro: sudo pacman -S gtk4 libadwaita python-gobject"
    echo "  Fedora: sudo dnf install gtk4 libadwaita python3-gobject"
    echo "  Ubuntu/Debian: sudo apt install libgtk-4-1 libadwaita-1-0 python3-gi"
    exit 1
fi
echo -e "${GREEN}✓ GTK4 found${NC}"

# Check for D-Bus Python bindings
if ! python3 -c "import dbus" 2>/dev/null; then
    echo -e "${RED}✗ D-Bus Python bindings not found${NC}"
    echo ""
    echo "Please install D-Bus dependencies:"
    echo "  Arch/Manjaro: sudo pacman -S python-dbus"
    echo "  Fedora: sudo dnf install python3-dbus"
    echo "  Ubuntu/Debian: sudo apt install python3-dbus"
    echo ""
    echo "If you get build errors, also install:"
    echo "  Ubuntu/Debian: sudo apt install python3-dev python3-dbus-dev libdbus-1-dev libdbus-glib-1-dev build-essential pkg-config cmake"
    exit 1
fi
echo -e "${GREEN}✓ D-Bus Python bindings found${NC}"

# Get installation directory
INSTALL_DIR="$HOME/.local/share/physica-app"
BIN_DIR="$HOME/.local/bin"

echo ""
echo -e "${YELLOW}➜ Installation directories:${NC}"
echo "  App: $INSTALL_DIR"
echo "  Bin: $BIN_DIR"
echo ""

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$HOME/.config/autostart"

echo -e "${YELLOW}➜ Copying files...${NC}"

# Copy service files
cp -r service "$INSTALL_DIR/"
cp -r gtk-app "$INSTALL_DIR/"
cp -r scripts "$INSTALL_DIR/"
cp run_service.sh "$INSTALL_DIR/"

echo -e "${GREEN}✓ Files copied${NC}"

# Create virtual environment
echo ""
echo -e "${YELLOW}➜ Creating virtual environment...${NC}"

cd "$INSTALL_DIR"
python3 -m venv venv

echo -e "${GREEN}✓ Virtual environment created${NC}"

# Install Python dependencies
echo ""
echo -e "${YELLOW}➜ Installing Python dependencies...${NC}"

# Check if we need to install system packages
if ! python3 -c "import dbus" 2>/dev/null || ! python3 -c "import gi" 2>/dev/null || ! python3 -c "import cairo" 2>/dev/null; then
    echo -e "${YELLOW}  Installing required system packages...${NC}"
    
    # Detect package manager and install system packages
    if command -v apt &> /dev/null; then
        echo "  Installing system packages via apt..."
        sudo apt install -y python3-dbus python3-gi python3-cairo python3-pyudev
    elif command -v pacman &> /dev/null; then
        echo "  Installing system packages via pacman..."
        sudo pacman -S --noconfirm python-dbus python-gobject python-cairo python-pyudev
    elif command -v dnf &> /dev/null; then
        echo "  Installing system packages via dnf..."
        sudo dnf install -y python3-dbus python3-gobject python3-cairo python3-pyudev
    fi
fi

# Activate venv and install dependencies
source "$INSTALL_DIR/venv/bin/activate"

pip install --upgrade pip > /dev/null 2>&1

cd "$INSTALL_DIR/service"
pip install -r requirements.txt

cd "$INSTALL_DIR/gtk-app"
pip install -r requirements.txt

deactivate

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create launcher scripts
echo ""
echo -e "${YELLOW}➜ Creating launcher scripts...${NC}"

# Service launcher
cat > "$BIN_DIR/physica-service" << 'EOF'
#!/bin/bash
VENV="$HOME/.local/share/physica-app/venv"
cd "$HOME/.local/share/physica-app/service"
exec "$VENV/bin/python" -u main.py "$@"
EOF
chmod +x "$BIN_DIR/physica-service"

# GUI launcher
cat > "$BIN_DIR/physica" << 'EOF'
#!/bin/bash
VENV="$HOME/.local/share/physica-app/venv"
cd "$HOME/.local/share/physica-app/gtk-app"
exec "$VENV/bin/python" run.py "$@"
EOF
chmod +x "$BIN_DIR/physica"

echo -e "${GREEN}✓ Launchers created${NC}"

# Create desktop entry
echo ""
echo -e "${YELLOW}➜ Creating desktop entry...${NC}"

cat > "$HOME/.local/share/applications/physica.desktop" << EOF
[Desktop Entry]
Name=Physica
Comment=Physical Game Cartridge Manager
Exec=$BIN_DIR/physica
Icon=applications-games
Terminal=false
Type=Application
Categories=Game;Utility;
Keywords=games;cartridge;usb;steam;
EOF

echo -e "${GREEN}✓ Desktop entry created${NC}"

# Create autostart for service
echo ""
echo -e "${YELLOW}➜ Setting up service autostart...${NC}"

cat > "$HOME/.config/autostart/physica-service.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Physica Service
Exec=$BIN_DIR/physica-service
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
Comment=Physica background service for cartridge management
EOF

echo -e "${GREEN}✓ Autostart configured${NC}"

# Create default config if it doesn't exist
CONFIG_DIR="$HOME/.config/physica"
if [ ! -f "$CONFIG_DIR/config.toml" ]; then
    echo ""
    echo -e "${YELLOW}➜ Creating default configuration...${NC}"
    mkdir -p "$CONFIG_DIR"
    
    cat > "$CONFIG_DIR/config.toml" << 'EOF'
[service]
scan_interval = 5
mount_base = "/media/deck"
auto_launch_delay = 2

[wine]
default_version = "GE-Proton10-17"
search_paths = [
    "~/.steam/steam/steamapps/common",
    "~/.local/share/Steam/compatibilitytools.d"
]
EOF
    
    echo -e "${GREEN}✓ Default config created${NC}"
else
    echo -e "${GREEN}✓ Config already exists${NC}"
fi

# Check if ~/.local/bin is in PATH
echo ""
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}⚠ Warning: $HOME/.local/bin is not in your PATH${NC}"
    echo ""
    echo "Add this line to your ~/.bashrc (or ~/.zshrc):"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Then run: source ~/.bashrc"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║             ✅ Installation Complete!                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}🎮 Physica is now installed!${NC}"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Start the service (will auto-start on next login):"
echo "   $ physica-service"
echo ""
echo "2. In a new terminal, launch the GUI:"
echo "   $ physica"
echo ""
echo "3. Or find 'Physica' in your application menu"
echo ""
echo "4. Create your first cartridge with the Import Wizard!"
echo ""
echo "📚 Documentation: $INSTALL_DIR/README.md"
echo "🐛 Issues: https://github.com/parkerHurst/Physica/issues"
echo ""
echo "Happy gaming! 🎮✨"

