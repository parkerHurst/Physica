# 📦 Physica Distribution Guide

This guide explains how to package and distribute Physica for early access testing and beyond.

---

## 🎯 Quick Start: Package for Early Access

### 1. Create Distribution Package

```bash
./package.sh
```

This creates:
- `build/physica-1.0-EA.tar.gz` - The distribution package
- `build/physica-1.0-EA.tar.gz.sha256` - Checksum for verification

### 2. Distribute to Testers

Upload the `.tar.gz` file to:
- GitHub Releases
- Your website
- File sharing service (Google Drive, Dropbox, etc.)

### 3. Tester Installation Instructions

Provide testers with these instructions:

```bash
# 1. Download the package
wget https://github.com/parkerHurst/Physica/releases/download/v1.0-EA/physica-1.0-EA.tar.gz

# 2. Verify checksum (optional but recommended)
sha256sum -c physica-1.0-EA.tar.gz.sha256

# 3. Extract
tar -xzf physica-1.0-EA.tar.gz
cd physica-1.0-EA

# 4. Install
./install.sh

# 5. Run
physica-service  # In one terminal
physica          # In another terminal
```

---

## 📋 Distribution Methods

### Method 1: **Tarball** (Recommended for Early Access) ✅

**Best for:** Early access, testing, quick distribution

**Pros:**
- Simple to create and distribute
- Easy to update
- Small file size (~1-2 MB)
- Works on any Linux distro

**Cons:**
- Requires Python dependencies to be installed
- No automatic updates
- Manual installation

**Create:**
```bash
./package.sh
```

**Distribution:**
```bash
# Upload to GitHub Releases
gh release create v1.0-EA build/physica-1.0-EA.tar.gz

# Or use the GitHub web UI
```

---

### Method 2: **AppImage** (Single-File Executable)

**Best for:** Maximum portability, no dependency issues

**Pros:**
- Single file, runs anywhere
- No installation needed
- Bundles all dependencies

**Cons:**
- Large file size (~200-300 MB)
- Complex to create for GTK apps
- Requires additional tools

**Create:**

**Note:** AppImage creation for Python GTK apps is complex. Consider using this after early access phase.

```bash
# Install AppImage tools
pip install --user appimage-builder

# Create AppImage recipe
cat > AppImageBuilder.yml << 'EOF'
version: 1
AppDir:
  path: ./AppDir
  app_info:
    id: com.physica.app
    name: Physica
    icon: applications-games
    version: 1.0-EA
    exec: usr/bin/physica
    
  apt:
    arch: amd64
    sources:
      - sourceline: 'deb http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse'
    
    include:
      - python3.11
      - python3-gi
      - gir1.2-gtk-4.0
      - gir1.2-adwaita-1

  files:
    exclude:
      - usr/share/doc
      - usr/share/man

AppImage:
  arch: x86_64
  update-information: None
EOF

# Build AppImage
appimage-builder --recipe AppImageBuilder.yml
```

---

### Method 3: **Flatpak** (Modern Linux Package)

**Best for:** Long-term distribution, Linux desktop users

**Pros:**
- Sandboxed and secure
- Automatic dependency management
- Distribution through Flathub
- Automatic updates

**Cons:**
- More complex setup
- Requires Flatpak manifest
- Larger initial download

**Create:**

**Note:** Flatpak is recommended for stable releases, not early access.

1. Create Flatpak manifest (`com.physica.app.yml`)
2. Build with `flatpak-builder`
3. Submit to Flathub

See: https://docs.flatpak.org/en/latest/

---

### Method 4: **AUR Package** (Arch Linux)

**Best for:** Arch Linux users (Steam Deck included)

**Pros:**
- Native Arch installation
- Easy for Arch users
- Automatic updates via AUR helpers

**Cons:**
- Arch-only
- Requires PKGBUILD maintenance

**Create:**

```bash
# Create PKGBUILD
cat > PKGBUILD << 'EOF'
# Maintainer: Your Name <your@email.com>
pkgname=physica-git
pkgver=1.0.EA
pkgrel=1
pkgdesc="Physical Game Cartridge Manager for Steam Deck"
arch=('any')
url="https://github.com/parkerHurst/Physica"
license=('MIT')
depends=('python' 'python-dbus' 'python-pyudev' 'python-psutil' 
         'python-toml' 'python-gobject' 'gtk4' 'libadwaita')
makedepends=('git')
source=("git+https://github.com/parkerHurst/Physica.git")
sha256sums=('SKIP')

package() {
    cd "$srcdir/Physica"
    
    # Install to /opt
    install -dm755 "$pkgdir/opt/physica"
    cp -r service gtk-app scripts "$pkgdir/opt/physica/"
    
    # Install launchers
    install -Dm755 "install.sh" "$pkgdir/usr/share/physica/install.sh"
    
    # Install desktop entry
    install -Dm644 "physica.desktop" "$pkgdir/usr/share/applications/physica.desktop"
}
EOF

# Test build
makepkg -si

# Publish to AUR
# See: https://wiki.archlinux.org/title/AUR_submission_guidelines
```

---

## 📊 Comparison Table

| Method | Ease | Size | Portability | Dependencies | Updates |
|--------|------|------|-------------|--------------|---------|
| **Tarball** | ⭐⭐⭐⭐⭐ | 1-2 MB | ⭐⭐⭐⭐ | Manual | Manual |
| **AppImage** | ⭐⭐⭐ | 200-300 MB | ⭐⭐⭐⭐⭐ | None | Manual |
| **Flatpak** | ⭐⭐ | 50-100 MB | ⭐⭐⭐⭐⭐ | Auto | Auto |
| **AUR** | ⭐⭐⭐⭐ | N/A | ⭐⭐ (Arch only) | Auto | Auto |

---

## 🚀 Recommended Path

### Phase 1: Early Access (Now) ✅
- **Use:** Tarball distribution
- **Upload to:** GitHub Releases
- **Why:** Fast, simple, easy to update

### Phase 2: Wider Testing
- **Add:** AUR package (for Arch/Steam Deck users)
- **Why:** Easier for target audience

### Phase 3: Stable Release
- **Add:** Flatpak (Flathub)
- **Why:** Broad Linux support, professional distribution

### Phase 4: Maximum Compatibility
- **Add:** AppImage
- **Why:** Works everywhere, offline-friendly

---

## 📝 Creating a GitHub Release

### 1. Tag the version

```bash
git tag -a v1.0-EA -m "Version 1.0 Early Access"
git push origin v1.0-EA
```

### 2. Create package

```bash
./package.sh
```

### 3. Create release on GitHub

Go to: https://github.com/parkerHurst/Physica/releases/new

- **Tag:** v1.0-EA
- **Title:** Physica v1.0 - Early Access
- **Description:**
  ```markdown
  # 🎮 Physica v1.0 Early Access
  
  First public release of Physica - Physical Game Cartridge Manager!
  
  ## ✨ Features
  - Plug-and-play game cartridges
  - Memory card manager UI
  - Import wizard with automatic USB formatting
  - Playtime tracking
  - Toast notifications
  
  ## 📋 Installation
  
  1. Download `physica-1.0-EA.tar.gz`
  2. Extract: `tar -xzf physica-1.0-EA.tar.gz`
  3. Install: `cd physica-1.0-EA && ./install.sh`
  4. Run: `physica-service` then `physica`
  
  ## 🐛 Known Issues
  - Some Proton games may not work (check ProtonDB)
  - Service must be started manually (auto-start on next login)
  
  ## 📚 Documentation
  See README.md in the package for full documentation.
  
  **Tested on:** Arch Linux, Steam Deck (Desktop Mode)
  ```

- **Attach files:**
  - `build/physica-1.0-EA.tar.gz`
  - `build/physica-1.0-EA.tar.gz.sha256`

### 4. Announce

Share the release link:
- Reddit: r/SteamDeck, r/linux_gaming
- Discord: Steam Deck communities
- Twitter/Mastodon
- Your blog/website

---

## 🎯 Early Access Checklist

Before distributing:

- [x] Code is cleaned up
- [x] README is complete
- [x] Installation script works
- [x] Uninstall script works
- [ ] Test on fresh system
- [ ] Create GitHub release
- [ ] Write release notes
- [ ] Test download and install process
- [ ] Announce to community

---

## 🔧 Testing the Package

Before distributing, test on a clean system:

```bash
# Option 1: Test in Docker
docker run -it --rm archlinux:latest bash
# Then download and install the package

# Option 2: Test on VM
# Create a fresh Arch/Ubuntu VM and test installation

# Option 3: Test on another machine
# Copy to a different computer and install
```

---

## 📧 Support for Testers

Create clear support channels:
- **Issues:** GitHub Issues for bug reports
- **Discussions:** GitHub Discussions for questions
- **Discord:** Optional community server
- **Email:** Your contact for critical issues

Provide this to testers:
```markdown
## 🐛 Found a bug?

1. Check existing issues: https://github.com/parkerHurst/Physica/issues
2. If new, create an issue with:
   - Your OS (Steam Deck, Arch, etc.)
   - Python version (`python3 --version`)
   - Steps to reproduce
   - Log output (service terminal)
   - Screenshots if UI-related

## ❓ Have questions?

Use GitHub Discussions: https://github.com/parkerHurst/Physica/discussions
```

---

## 🎉 You're Ready!

Your Physica app is now ready for early access distribution. The tarball method is perfect for initial testing - simple, fast, and easy to iterate on based on feedback.

Good luck with your early access launch! 🚀

