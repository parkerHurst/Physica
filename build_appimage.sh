#!/bin/bash
# Build Physica AppImage for Steam Deck
# This script creates a self-contained AppImage with bundled GTK4/libadwaita

set -e

VERSION="1.1.2"
APP_NAME="Physica"
APPIMAGE_NAME="${APP_NAME}-${VERSION}-STEAMDECK.AppImage"
BUILD_DIR="build_appimage"
APP_DIR="${BUILD_DIR}/AppDir"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          Building Physica AppImage for Steam Deck          ║"
echo "║                      Version ${VERSION}                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Clean up old build
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning old build directory..."
    rm -rf "$BUILD_DIR"
fi

# Create AppDir structure
echo "Creating AppDir structure..."
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/lib"
mkdir -p "${APP_DIR}/usr/lib/girepository-1.0"
mkdir -p "${APP_DIR}/usr/share/applications"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${APP_DIR}/usr/share/physica"
mkdir -p "${APP_DIR}/usr/lib/python3.13/site-packages"

# Copy application files
echo "Copying application files..."
cp -r gtk-app/physica_gtk "${APP_DIR}/usr/share/physica/"
cp -r service "${APP_DIR}/usr/share/physica/"
cp -r scripts "${APP_DIR}/usr/share/physica/"
cp gtk-app/__init__.py "${APP_DIR}/usr/share/physica/"
cp service/__init__.py "${APP_DIR}/usr/share/physica/"
cp physica.svg "${APP_DIR}/usr/share/icons/hicolor/scalable/apps/physica.svg"

# Copy icon at multiple sizes for AppDir
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/64x64/apps"
cp physica.svg "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/physica.svg"
cp physica.svg "${APP_DIR}/usr/share/icons/hicolor/128x128/apps/physica.svg"
cp physica.svg "${APP_DIR}/usr/share/icons/hicolor/64x64/apps/physica.svg"

# Create Desktop entry
cat > "${APP_DIR}/usr/share/applications/physica.desktop" <<'EOF'
[Desktop Entry]
Name=Physica
Exec=physica
Icon=physica
Terminal=false
Type=Application
Categories=Game;Utility;
Keywords=games;cartridge;usb;steam;
Comment=Physical game cartridge manager
MimeType=
EOF

# Create symlink to desktop file in AppDir root (required by appimagetool)
# Use relative path for proper symlink
cd "${APP_DIR}"
ln -sf "usr/share/applications/physica.desktop" "Physica.desktop"
# Copy icon to AppDir root for appimagetool
cp usr/share/icons/hicolor/scalable/apps/physica.svg physica.svg
cd - > /dev/null

# Create AppRun script
cat > "${APP_DIR}/AppRun" <<'EOFAPP'
#!/bin/bash
# Physica AppRun - Launches Physica in the AppImage

# Get directory where AppImage is mounted
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${HERE}/usr/local/bin:${PATH}"

# Set library paths for bundled GTK4
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Find python in usr/bin or use system python
PYTHON="$(which python3)"

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3 not found!"
    exit 1
fi

# Set environment variables
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export PHYSICA_INSTALL_DIR="${HERE}/usr/share/physica"

# Add AppDir Python modules to path
export PYTHONPATH="${HERE}/usr/lib/python3.13/site-packages:${HERE}/usr/share/physica:${PYTHONPATH}"

# Set GI typelib path for GObject introspection
export GI_TYPELIB_PATH="${HERE}/usr/lib/girepository-1.0"

# Launch Physica
exec "${PYTHON}" -u "${HERE}/usr/share/physica/physica_gtk/main.py" "$@"
EOFAPP

chmod +x "${APP_DIR}/AppRun"

# Bundle Python dependencies
echo "Bundling Python dependencies..."

# Store the current directory
SCRIPT_DIR="$(pwd)"

cd "${APP_DIR}/usr"

# Create a temporary virtual environment to bundle dependencies
python3 -m venv temp_venv
source temp_venv/bin/activate

pip install --upgrade pip --quiet
pip install dbus-python PyGObject pycairo pyudev psutil toml --quiet

# Copy required Python modules to AppDir
echo "Copying Python packages..."
# Find the venv's site-packages directory
VENV_SITE_PKGS=$(find temp_venv/lib/python3* -name "site-packages" -type d | head -1)

echo "Found site-packages at: $VENV_SITE_PKGS"

if [ -n "$VENV_SITE_PKGS" ] && [ -d "$VENV_SITE_PKGS" ]; then
    # Copy all packages from venv site-packages  
    # We're in ${APP_DIR}/usr, so go up one level for the copy target
    TARGET_DIR="../usr/lib/python3.13/site-packages"
    mkdir -p "$TARGET_DIR"
    echo "Copying from $VENV_SITE_PKGS/* to $TARGET_DIR/"
    # Copy without verbose to avoid massive output
    cp -r "${VENV_SITE_PKGS}/"* "$TARGET_DIR/" 2>/dev/null
    echo "Verify: $(ls "$TARGET_DIR" | wc -l) items in target"
fi

# Copy shared libraries needed by Python modules
echo "Copying shared libraries..."
ldconfig -p 2>/dev/null | grep -E "libdbus-1|libgirepository|libcairo|libgobject|libglib" | awk '{print $NF}' | xargs -I {} sh -c 'cp {} "$1"/usr/lib/ 2>/dev/null || true' -- 

# Copy .so files from the venv site-packages (like _gi.cpython-xxx.so)
echo "Copying .so files..."
find temp_venv/lib/python3* -name "*.so" -exec cp {} "${APP_DIR}/usr/lib/python3.13/site-packages/" \; 2>/dev/null || true

deactivate
cd - > /dev/null

# Copy GI typelibs for GTK4 and libadwaita
echo "Copying GI typelibs..."
if [ -d "/usr/share/gir-1.0" ]; then
    # Find required gir files and copy them
    GIR_DIRS=("/usr/share/gir-1.0" "/usr/lib/girepository-1.0")
    for dir in "${GIR_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            # Copy GTK4, Adw, Gio, Gdk related files
            find "$dir" -name "Gtk-4.0.typelib" -exec cp {} "${APP_DIR}/usr/lib/girepository-1.0/" \; 2>/dev/null || true
            find "$dir" -name "Adw-1.typelib" -exec cp {} "${APP_DIR}/usr/lib/girepository-1.0/" \; 2>/dev/null || true
            find "$dir" -name "Gio-2.0.typelib" -exec cp {} "${APP_DIR}/usr/lib/girepository-1.0/" \; 2>/dev/null || true
            find "$dir" -name "Gdk-4.0.typelib" -exec cp {} "${APP_DIR}/usr/lib/girepository-1.0/" \; 2>/dev/null || true
            find "$dir" -name "GLib-2.0.typelib" -exec cp {} "${APP_DIR}/usr/lib/girepository-1.0/" \; 2>/dev/null || true
        fi
    done
fi

echo "⚠️  Note: This AppImage now includes GTK4 typelibs but still requires GTK4 libraries on the host system"
echo "For Steam Deck: GTK4 is typically available in Desktop Mode"

# Download appimagetool if not present
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget -q -O appimagetool-x86_64.AppImage \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# Build the AppImage
echo "Building AppImage..."
./appimagetool-x86_64.AppImage \
    "${APP_DIR}" \
    "${APPIMAGE_NAME}" \
    2>&1 | grep -v "^WARNING:" || true

# Move AppImage to build directory
if [ -f "${APPIMAGE_NAME}" ]; then
    mv "${APPIMAGE_NAME}" "${BUILD_DIR}/"
fi

# Make it executable
if [ -f "${BUILD_DIR}/${APPIMAGE_NAME}" ]; then
    chmod +x "${BUILD_DIR}/${APPIMAGE_NAME}"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║             ✅ AppImage Created Successfully!             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Location: ${BUILD_DIR}/${APPIMAGE_NAME}"
echo ""
echo "Requirements for running the AppImage:"
echo "  - Python 3.11+"
echo "  - GTK4 and libadwaita (install via system package manager)"
echo ""
echo "To run:"
echo "  chmod +x ${BUILD_DIR}/${APPIMAGE_NAME}"
echo "  ./${BUILD_DIR}/${APPIMAGE_NAME}"
echo ""
echo "For Steam Deck users:"
echo "  GTK4 is typically available in SteamOS Desktop Mode"
echo "  If not installed, you may need to install it via pacman (read-only root)"
echo ""

