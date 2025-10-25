#!/bin/bash
# Install Physica service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Installing Physica Service ==="
echo

# Check if running as root for system installation
if [ "$EUID" -eq 0 ]; then
    INSTALL_TYPE="system"
    SERVICE_DIR="/usr/lib/systemd/system"
    BIN_DIR="/usr/bin"
    LIB_DIR="/usr/lib/physica"
else
    INSTALL_TYPE="user"
    SERVICE_DIR="$HOME/.config/systemd/user"
    BIN_DIR="$HOME/.local/bin"
    LIB_DIR="$HOME/.local/lib/physica"
fi

echo "Installation type: $INSTALL_TYPE"
echo "Service directory: $SERVICE_DIR"
echo "Binary directory: $BIN_DIR"
echo "Library directory: $LIB_DIR"
echo

# Install dependencies
echo "Installing Python dependencies..."
cd "$PROJECT_ROOT/service"
pip install --user -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p "$SERVICE_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$LIB_DIR"

# Copy service files
echo "Copying service files..."
cp -r "$PROJECT_ROOT/service/"* "$LIB_DIR/"

# Create launcher script
echo "Creating launcher script..."
cat > "$BIN_DIR/physica-service" <<EOF
#!/usr/bin/env python3
import sys
sys.path.insert(0, '$LIB_DIR')
from main import main

if __name__ == '__main__':
    main()
EOF
chmod +x "$BIN_DIR/physica-service"

# Install systemd service
echo "Installing systemd service..."
if [ "$INSTALL_TYPE" = "system" ]; then
    cp "$PROJECT_ROOT/physica.service" "$SERVICE_DIR/"
    systemctl daemon-reload
    echo
    echo "✓ Service installed!"
    echo
    echo "To enable and start the service:"
    echo "  sudo systemctl enable physica.service"
    echo "  sudo systemctl start physica.service"
else
    # Modify service file for user installation
    sed "s|/usr/bin/python3|$BIN_DIR/physica-service|g" "$PROJECT_ROOT/physica.service" > "$SERVICE_DIR/physica.service"
    systemctl --user daemon-reload
    echo
    echo "✓ Service installed!"
    echo
    echo "To enable and start the service:"
    echo "  systemctl --user enable physica.service"
    echo "  systemctl --user start physica.service"
fi

echo
echo "To view logs:"
if [ "$INSTALL_TYPE" = "system" ]; then
    echo "  sudo journalctl -u physica.service -f"
else
    echo "  journalctl --user -u physica.service -f"
fi

