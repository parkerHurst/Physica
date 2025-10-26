# Physica Flatpak Distribution

This directory contains the Flatpak configuration files for distributing Physica as a sandboxed application.

**Website:** [physica-app.org](https://physica-app.org)

## Files

- `io.github.physica.app.yml` - Flatpak manifest defining the application build process
- `physica.desktop` - Desktop entry file for the application
- `physica.svg` - Application icon
- `build_flatpak.sh` - Build script for creating and installing the Flatpak

## Building and Installing

### Prerequisites

Install Flatpak and flatpak-builder:

```bash
# Arch Linux
sudo pacman -S flatpak flatpak-builder

# Ubuntu/Debian
sudo apt install flatpak flatpak-builder

# Fedora
sudo dnf install flatpak flatpak-builder
```

### Build and Install

Run the build script from the project root:

```bash
./build_flatpak.sh
```

This will:
1. Set up the Flathub repository
2. Install GNOME runtime and SDK
3. Build the Physica Flatpak
4. Install it locally

### Running

```bash
flatpak run io.github.physica.app
```

### Uninstalling

```bash
flatpak uninstall io.github.physica.app
```

## Permissions

The Flatpak manifest includes the following permissions:

- **Filesystem access**: Home directory, host filesystem (for USB drives), and read-only access to `/media`, `/run/media`, and `/mnt`
- **D-Bus access**: System bus, session bus, UDisks2, and systemd
- **Device access**: DRI (for graphics) and all devices (for USB)
- **Owned D-Bus names**: `com.physica.Service` and `com.physica.App`

## Publishing to Flathub

To publish to Flathub:

1. Fork the [Flathub repository](https://github.com/flathub/flathub)
2. Create a new directory: `io.github.physica.app`
3. Copy the manifest and related files
4. Submit a pull request

## Troubleshooting

### USB Drive Access Issues

If USB drives aren't detected:

```bash
# Check if UDisks2 is running
systemctl --user status udisks2

# Check Flatpak permissions
flatpak info io.github.physica.app
```

### D-Bus Service Issues

If the D-Bus service fails to start:

```bash
# Check systemd user services
systemctl --user status physica-service

# Check D-Bus service registration
busctl --user list | grep physica
```

## Development

For development builds:

```bash
# Build without installing
flatpak-builder build flatpak/io.github.physica.app.yml

# Run from build directory
flatpak-builder --run build flatpak/io.github.physica.app.yml physica
```
