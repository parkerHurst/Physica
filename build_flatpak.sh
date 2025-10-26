#!/bin/bash

# Physica Flatpak Build Script
# This script builds and installs Physica as a Flatpak application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║               Physica Flatpak Build Script                 ║${NC}"
echo -e "${BLUE}║         Physical Game Cartridge Manager for Linux          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if flatpak is installed
if ! command -v flatpak &> /dev/null; then
    echo -e "${RED}❌ Flatpak is not installed${NC}"
    echo "Please install Flatpak first:"
    echo "  Arch: sudo pacman -S flatpak"
    echo "  Ubuntu/Debian: sudo apt install flatpak"
    echo "  Fedora: sudo dnf install flatpak"
    exit 1
fi

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    echo -e "${RED}❌ flatpak-builder is not installed${NC}"
    echo "Please install flatpak-builder first:"
    echo "  Arch: sudo pacman -S flatpak-builder"
    echo "  Ubuntu/Debian: sudo apt install flatpak-builder"
    echo "  Fedora: sudo dnf install flatpak-builder"
    exit 1
fi

echo -e "${YELLOW}➜ Setting up Flatpak repository...${NC}"

# Add Flathub repository if not already added
if ! flatpak remote-list | grep -q flathub; then
    echo "Adding Flathub repository..."
    flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi

echo -e "${YELLOW}➜ Installing GNOME runtime and SDK...${NC}"

# Install GNOME runtime and SDK
flatpak install -y flathub org.gnome.Platform//45
flatpak install -y flathub org.gnome.Sdk//45

echo -e "${YELLOW}➜ Building Physica Flatpak...${NC}"

# Build the Flatpak
cd "$(dirname "$0")"
flatpak-builder --force-clean --install-deps-from=flathub build flatpak/org.physicaapp.Physica.yml

echo -e "${YELLOW}➜ Installing Physica Flatpak...${NC}"

# Install the built Flatpak
flatpak-builder --user --install --force-clean build flatpak/org.physicaapp.Physica.yml

echo -e "${GREEN}✓ Physica Flatpak installed successfully!${NC}"
echo ""
echo -e "${BLUE}To run Physica:${NC}"
echo "  flatpak run org.physicaapp.Physica"
echo ""
echo -e "${BLUE}To uninstall:${NC}"
echo "  flatpak uninstall org.physicaapp.Physica"
echo ""
echo -e "${BLUE}To update:${NC}"
echo "  flatpak update org.physicaapp.Physica"
