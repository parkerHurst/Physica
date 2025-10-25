#!/bin/bash
# Package Physica for distribution
# Creates a tarball that can be shared with early access testers

set -e

VERSION="1.0-EA"
PACKAGE_NAME="physica-$VERSION"
BUILD_DIR="build/$PACKAGE_NAME"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          Physica Packaging Script v$VERSION                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Clean previous builds
echo "➜ Cleaning previous builds..."
rm -rf build/
mkdir -p "$BUILD_DIR"

# Copy necessary files
echo "➜ Copying files..."
cp -r service "$BUILD_DIR/"
cp -r gtk-app "$BUILD_DIR/"
cp -r scripts "$BUILD_DIR/"
cp run_service.sh "$BUILD_DIR/"
cp install.sh "$BUILD_DIR/"
cp uninstall.sh "$BUILD_DIR/"
cp README.md "$BUILD_DIR/"
cp CONTRIBUTING.md "$BUILD_DIR/"
cp .gitignore "$BUILD_DIR/"

# Make scripts executable
chmod +x "$BUILD_DIR/install.sh"
chmod +x "$BUILD_DIR/uninstall.sh"
chmod +x "$BUILD_DIR/run_service.sh"

# Remove __pycache__ and .pyc files
echo "➜ Cleaning Python cache..."
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

# Create tarball
echo "➜ Creating tarball..."
cd build
tar -czf "$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME/"
cd ..

# Create checksum
echo "➜ Generating checksum..."
cd build
sha256sum "$PACKAGE_NAME.tar.gz" > "$PACKAGE_NAME.tar.gz.sha256"
cd ..

# Get size
SIZE=$(du -h "build/$PACKAGE_NAME.tar.gz" | cut -f1)

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ Package Created Successfully!               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Package: build/$PACKAGE_NAME.tar.gz"
echo "📊 Size: $SIZE"
echo "🔐 SHA256: build/$PACKAGE_NAME.tar.gz.sha256"
echo ""
echo "📋 Distribution instructions for testers:"
echo ""
echo "1. Extract the archive:"
echo "   $ tar -xzf $PACKAGE_NAME.tar.gz"
echo "   $ cd $PACKAGE_NAME"
echo ""
echo "2. Run the installer:"
echo "   $ ./install.sh"
echo ""
echo "3. Follow the on-screen instructions"
echo ""
echo "🚀 Ready to distribute!"

