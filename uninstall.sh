#!/bin/bash
# Physica Uninstallation Script

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          Physica Uninstallation Script                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}✗ Please do NOT run this script as root${NC}"
    exit 1
fi

echo -e "${YELLOW}This will remove Physica from your system.${NC}"
echo "Your cartridges and game data will NOT be deleted."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}➜ Stopping service...${NC}"
pkill -f "python.*physica.*main.py" 2>/dev/null || true
echo -e "${GREEN}✓ Service stopped${NC}"

echo -e "${YELLOW}➜ Removing files...${NC}"

# Remove installation directory
rm -rf "$HOME/.local/share/physica"
echo "  ✓ App files removed"

# Remove launchers
rm -f "$HOME/.local/bin/physica"
rm -f "$HOME/.local/bin/physica-service"
echo "  ✓ Launchers removed"

# Remove desktop entry
rm -f "$HOME/.local/share/applications/physica.desktop"
echo "  ✓ Desktop entry removed"

# Remove autostart
rm -f "$HOME/.config/autostart/physica-service.desktop"
echo "  ✓ Autostart removed"

echo -e "${GREEN}✓ All files removed${NC}"

echo ""
echo "📝 Note: Configuration and game data preserved at:"
echo "   Config: ~/.config/physica/"
echo "   Game data: ~/.local/share/physica/"
echo ""
echo "To completely remove all Physica data:"
echo "   rm -rf ~/.config/physica"
echo "   rm -rf ~/.local/share/physica"
echo ""
echo "⚠️  This will NOT delete your game cartridges (USB drives)"
echo ""
echo -e "${GREEN}✅ Physica uninstalled successfully${NC}"

