#!/bin/bash
# Script to create a test game cartridge structure

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <mount_path> [game_name]"
    echo "Example: $0 /media/deck/TEST_GAME 'Hollow Knight'"
    exit 1
fi

MOUNT_PATH="$1"
GAME_NAME="${2:-Test Game}"
GAME_ID=$(echo "$GAME_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
UUID=$(uuidgen)

echo "Creating test cartridge at: $MOUNT_PATH"
echo "Game name: $GAME_NAME"
echo "Game ID: $GAME_ID"
echo "UUID: $UUID"
echo

# Create directory structure
mkdir -p "$MOUNT_PATH/.gamecard"
mkdir -p "$MOUNT_PATH/game"
mkdir -p "$MOUNT_PATH/prefix"
mkdir -p "$MOUNT_PATH/savedata"

# Create metadata.toml
cat > "$MOUNT_PATH/.gamecard/metadata.toml" <<EOF
[game]
name = "$GAME_NAME"
id = "${GAME_ID}_test"
version = "1.0.0"
publisher = "Test Publisher"
release_date = "2024-01-01"
executable = "game/game.exe"
genre = "Test"

[runtime]
platform = "windows"
needs_wine = true
wine_version = "GE-Proton8-14"
launch_args = []
working_directory = "game"
save_paths = [
    "drive_c/users/steamuser/AppData/Local/${GAME_ID}_test",
    "drive_c/users/steamuser/AppData/Roaming/${GAME_ID}_test"
]

[cartridge]
formatted_date = "$(date -Iseconds)"
uuid = "$UUID"
total_playtime = 0
last_played = ""
play_count = 0
notes = "Test cartridge created by create_test_cartridge.sh"

[import]
source = "directory"
import_date = "$(date -Iseconds)"
original_size = 0
source_path = "/test/path"
EOF

# Create a dummy executable
cat > "$MOUNT_PATH/game/game.exe" <<'EOF'
#!/bin/bash
echo "Test game started"
sleep 300  # Run for 5 minutes
echo "Test game ended"
EOF
chmod +x "$MOUNT_PATH/game/game.exe"

echo "✓ Test cartridge created successfully!"
echo
echo "Cartridge details:"
echo "  Location: $MOUNT_PATH"
echo "  UUID: $UUID"
echo "  Metadata: $MOUNT_PATH/.gamecard/metadata.toml"
echo
echo "You can now test the scanner with:"
echo "  cd service && python -m physica.cartridge_scanner"

