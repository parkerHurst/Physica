#!/bin/bash
# Interactive script to set up a real game cartridge

set -e

echo "=== Physica Real Game Cartridge Setup ==="
echo ""

# Check if running as root for mount operations
if [ "$EUID" -eq 0 ]; then
    echo "Error: Don't run this script as root!"
    echo "Run as normal user - it will ask for sudo when needed."
    exit 1
fi

# Get game source directory
read -p "Path to installed game directory: " GAME_SOURCE
if [ ! -d "$GAME_SOURCE" ]; then
    echo "Error: Directory $GAME_SOURCE does not exist!"
    exit 1
fi

# Get game name
read -p "Game name: " GAME_NAME
GAME_ID=$(echo "$GAME_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')

# Get mount point
read -p "Cartridge mount point [/media/deck/${GAME_ID^^}]: " MOUNT_POINT
MOUNT_POINT=${MOUNT_POINT:-/media/deck/${GAME_ID^^}}

# Check if already mounted
if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
    echo "✓ $MOUNT_POINT is already mounted"
else
    echo "Error: $MOUNT_POINT is not mounted!"
    echo "Please format and mount your USB drive first."
    echo "See REAL_GAME_SETUP.md for instructions."
    exit 1
fi

# Generate UUID
UUID=$(uuidgen)

echo ""
echo "=== Configuration ==="
echo "Game Name: $GAME_NAME"
echo "Game ID: $GAME_ID"
echo "Source: $GAME_SOURCE"
echo "Cartridge: $MOUNT_POINT"
echo "UUID: $UUID"
echo ""

# Confirm
read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Aborted."
    exit 0
fi

# Create directory structure
echo ""
echo "Creating cartridge structure..."
mkdir -p "$MOUNT_POINT/.gamecard"
mkdir -p "$MOUNT_POINT/game"
mkdir -p "$MOUNT_POINT/prefix"
mkdir -p "$MOUNT_POINT/savedata"
echo "✓ Directories created"

# Find executable
echo ""
echo "Searching for executable files..."
EXE_FILES=$(find "$GAME_SOURCE" -name "*.exe" -type f 2>/dev/null || true)

if [ -z "$EXE_FILES" ]; then
    echo "Warning: No .exe files found in $GAME_SOURCE"
    EXECUTABLE="game/unknown.exe"
else
    echo "Found executables:"
    echo "$EXE_FILES" | nl
    echo ""
    
    # If multiple, let user choose
    EXE_COUNT=$(echo "$EXE_FILES" | wc -l)
    if [ "$EXE_COUNT" -gt 1 ]; then
        read -p "Which executable? (1-$EXE_COUNT): " EXE_CHOICE
        SELECTED_EXE=$(echo "$EXE_FILES" | sed -n "${EXE_CHOICE}p")
    else
        SELECTED_EXE="$EXE_FILES"
    fi
    
    # Get relative path
    EXECUTABLE="game/$(basename "$SELECTED_EXE")"
    echo "Selected: $EXECUTABLE"
fi

# Detect installed Proton versions
echo ""
echo "Detecting Proton versions..."
PROTON_DIR="$HOME/.steam/steam/compatibilitytools.d"

if [ -d "$PROTON_DIR" ]; then
    PROTON_VERSIONS=$(ls -1 "$PROTON_DIR" 2>/dev/null | grep -i proton || true)
    
    if [ -z "$PROTON_VERSIONS" ]; then
        echo "Warning: No Proton versions found in $PROTON_DIR"
        WINE_VERSION="GE-Proton8-14"
    else
        echo "Found Proton versions:"
        echo "$PROTON_VERSIONS" | nl
        
        # Use first one as default
        DEFAULT_PROTON=$(echo "$PROTON_VERSIONS" | head -1)
        read -p "Proton version [$DEFAULT_PROTON]: " WINE_VERSION
        WINE_VERSION=${WINE_VERSION:-$DEFAULT_PROTON}
    fi
else
    echo "Warning: Proton directory not found"
    WINE_VERSION="GE-Proton8-14"
fi

echo "Using: $WINE_VERSION"

# Get game size
echo ""
echo "Calculating game size..."
GAME_SIZE=$(du -sb "$GAME_SOURCE" | cut -f1)
GAME_SIZE_HUMAN=$(du -sh "$GAME_SOURCE" | cut -f1)
echo "Game size: $GAME_SIZE_HUMAN"

# Check available space
AVAILABLE=$(df "$MOUNT_POINT" | tail -1 | awk '{print $4}')
AVAILABLE_BYTES=$((AVAILABLE * 1024))

if [ "$GAME_SIZE" -gt "$AVAILABLE_BYTES" ]; then
    echo "Error: Not enough space on cartridge!"
    echo "  Required: $GAME_SIZE_HUMAN"
    echo "  Available: $(df -h "$MOUNT_POINT" | tail -1 | awk '{print $4}')"
    exit 1
fi

echo "✓ Sufficient space available"

# Create metadata.toml
echo ""
echo "Creating metadata.toml..."
cat > "$MOUNT_POINT/.gamecard/metadata.toml" <<EOF
[game]
name = "$GAME_NAME"
id = "$GAME_ID"
version = "1.0.0"
publisher = ""
release_date = ""
executable = "$EXECUTABLE"
genre = ""

[runtime]
platform = "windows"
needs_wine = true
wine_version = "$WINE_VERSION"
launch_args = []
working_directory = "game"

[cartridge]
formatted_date = "$(date -Iseconds)"
uuid = "$UUID"
total_playtime = 0
last_played = ""
play_count = 0
notes = "Real game cartridge created $(date)"

[import]
source = "directory"
import_date = "$(date -Iseconds)"
original_size = $GAME_SIZE
source_path = "$GAME_SOURCE"
EOF

echo "✓ metadata.toml created"

# Copy game files
echo ""
echo "Copying game files (this may take a while)..."
echo "From: $GAME_SOURCE"
echo "To: $MOUNT_POINT/game/"
echo ""

if command -v rsync &> /dev/null; then
    rsync -avh --progress "$GAME_SOURCE/" "$MOUNT_POINT/game/"
else
    cp -rv "$GAME_SOURCE"/* "$MOUNT_POINT/game/"
fi

echo ""
echo "✓ Game files copied"

# Verify
echo ""
echo "Verifying cartridge structure..."
if [ -f "$MOUNT_POINT/.gamecard/metadata.toml" ] && \
   [ -d "$MOUNT_POINT/game" ] && \
   [ -d "$MOUNT_POINT/prefix" ]; then
    echo "✓ Cartridge structure verified"
else
    echo "Error: Cartridge structure incomplete!"
    exit 1
fi

# Test with Physica scanner
echo ""
echo "Testing with Physica scanner..."
cd "$(dirname "$0")/.."

if [ -f "./run_scanner.sh" ]; then
    # Update config to use /media/deck
    mkdir -p ~/.config/physica
    sed -i 's|mount_base = ".*"|mount_base = "/media/deck"|' ~/.config/physica/config.toml 2>/dev/null || true
    
    echo ""
    ./run_scanner.sh | grep -A 10 "$GAME_NAME" || true
fi

# Summary
echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Cartridge Details:"
echo "  Name: $GAME_NAME"
echo "  UUID: $UUID"
echo "  Location: $MOUNT_POINT"
echo "  Executable: $EXECUTABLE"
echo "  Proton: $WINE_VERSION"
echo ""
echo "Next steps:"
echo "  1. Update Physica config: ~/.config/physica/config.toml"
echo "     Set mount_base = \"/media/deck\""
echo ""
echo "  2. Start Physica service:"
echo "     cd $(dirname "$0")/.."
echo "     ./run_service.sh --debug"
echo ""
echo "  3. Launch game via D-Bus:"
echo "     dbus-send --session --print-reply \\"
echo "       --dest=org.physicaapp.Manager /org/physicaapp/Manager \\"
echo "       org.physicaapp.Manager.LaunchGame string:\"$UUID\""
echo ""
echo "See REAL_GAME_SETUP.md for detailed instructions."

