"""Import Wizard for creating game cartridges"""

import gi
import os
import subprocess
import threading
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio


class ImportWizardDialog(Adw.Window):
    """Multi-step wizard for importing games"""
    
    def __init__(self, parent):
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(800, 600)
        self.set_title("Import Game Cartridge")
        
        # Wizard state
        self.game_directory = None
        self.usb_mount_point = None
        self.auto_launch = True  # Default: auto-launch enabled
        
        # Build UI
        self._build_ui()
        
        # Show welcome page
        self._show_welcome_page()
    
    def _build_ui(self):
        """Build wizard UI"""
        # Main container
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header bar
        header = Adw.HeaderBar()
        self.content_box.append(header)
        
        # Content stack (wizard pages)
        self.pages = Gtk.Stack()
        self.pages.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.pages.set_vexpand(True)
        self.content_box.append(self.pages)
        
        # Action bar (navigation buttons)
        self.action_bar = Gtk.ActionBar()
        
        # Cancel button
        self.cancel_button = Gtk.Button(label="Cancel")
        self.cancel_button.connect("clicked", lambda *_: self.close())
        self.action_bar.pack_start(self.cancel_button)
        
        # Back button
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", self._on_back_clicked)
        self.action_bar.pack_end(self.back_button)
        
        # Next button
        self.next_button = Gtk.Button(label="Next")
        self.next_button.add_css_class("suggested-action")
        self.next_button.connect("clicked", self._on_next_clicked)
        self.action_bar.pack_end(self.next_button)
        
        self.content_box.append(self.action_bar)
        
        # Set window content
        self.set_content(self.content_box)
    
    def _show_welcome_page(self):
        """Show welcome page"""
        page = Adw.StatusPage()
        page.set_icon_name("media-optical-symbolic")
        page.set_title("Create Game Cartridge")
        page.set_description("Import a game from your computer to a USB drive.\nThe game will auto-launch when you insert the cartridge.")
        
        self.pages.add_named(page, "welcome")
        self.pages.set_visible_child_name("welcome")
        
        # Update buttons
        self.back_button.set_visible(False)
        self.next_button.set_label("Get Started")
        self.next_button.set_sensitive(True)
    
    def _show_game_selector_page(self):
        """Show game directory selection page"""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        page_box.set_margin_start(48)
        page_box.set_margin_end(48)
        page_box.set_margin_top(48)
        page_box.set_margin_bottom(48)
        page_box.set_halign(Gtk.Align.CENTER)
        page_box.set_valign(Gtk.Align.CENTER)
        
        # Title
        title = Gtk.Label(label="Select Game Directory")
        title.add_css_class("title-1")
        page_box.append(title)
        
        # Description
        desc = Gtk.Label(label="Choose the folder containing your game files")
        desc.add_css_class("dim-label")
        page_box.append(desc)
        
        # Selected path display
        # Restore previously selected directory if available
        if self.game_directory:
            initial_label = str(self.game_directory)
        else:
            initial_label = "No directory selected"
        
        self.game_path_label = Gtk.Label(label=initial_label)
        self.game_path_label.add_css_class("monospace")
        self.game_path_label.set_wrap(True)
        self.game_path_label.set_max_width_chars(50)
        page_box.append(self.game_path_label)
        
        # Browse button
        browse_button = Gtk.Button(label="Browse for Game Folder")
        browse_button.add_css_class("pill")
        browse_button.add_css_class("suggested-action")
        browse_button.set_size_request(200, -1)
        browse_button.connect("clicked", self._on_browse_game_clicked)
        page_box.append(browse_button)
        
        # Examples
        examples = Gtk.Label()
        examples.set_markup("<small>Examples:\n• ~/Games/Hollow Knight\n• ~/Games/Celeste\n• ~/Games/Stardew Valley</small>")
        examples.add_css_class("dim-label")
        page_box.append(examples)
        
        self.pages.add_named(page_box, "game_selector")
        self.pages.set_visible_child_name("game_selector")
        
        # Update buttons
        self.back_button.set_visible(True)
        self.next_button.set_label("Next")
        # Enable Next button if directory is already selected
        self.next_button.set_sensitive(self.game_directory is not None)
    
    def _on_browse_game_clicked(self, button):
        """Handle browse button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Game Directory")
        dialog.set_modal(True)
        
        # Select folder
        dialog.select_folder(
            parent=self,
            callback=self._on_game_folder_selected
        )
    
    def _on_game_folder_selected(self, dialog, result):
        """Handle game folder selection"""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                path = folder.get_path()
                self.game_directory = Path(path)
                self.game_path_label.set_label(str(self.game_directory))
                self.next_button.set_sensitive(True)
        except Exception as e:
            print(f"Error selecting folder: {e}")
    
    def _show_usb_selector_page(self):
        """Show USB drive selection page"""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        page_box.set_margin_start(48)
        page_box.set_margin_end(48)
        page_box.set_margin_top(48)
        page_box.set_margin_bottom(48)
        page_box.set_halign(Gtk.Align.CENTER)
        page_box.set_valign(Gtk.Align.CENTER)
        
        # Title
        title = Gtk.Label(label="Select USB Drive")
        title.add_css_class("title-1")
        page_box.append(title)
        
        # Description
        desc = Gtk.Label(label="Choose the USB drive to create the cartridge on")
        desc.add_css_class("dim-label")
        page_box.append(desc)
        
        # Warning
        warning = Gtk.Label()
        warning.set_markup("<b>⚠️ Warning:</b> Make sure this is the correct drive!\nThe cartridge will use the entire drive.")
        warning.add_css_class("warning")
        page_box.append(warning)
        
        # USB drive list
        self.usb_list_box = Gtk.ListBox()
        self.usb_list_box.add_css_class("boxed-list")
        self.usb_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.usb_list_box.connect("row-selected", self._on_usb_selected)
        
        # Scan for USB drives
        self._populate_usb_list()
        
        page_box.append(self.usb_list_box)
        
        # Refresh button
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", lambda *_: self._populate_usb_list())
        page_box.append(refresh_button)
        
        self.pages.add_named(page_box, "usb_selector")
        self.pages.set_visible_child_name("usb_selector")
        
        # Update buttons
        self.back_button.set_visible(True)
        self.next_button.set_label("Next")
        # Enable Next button if USB was already selected
        self.next_button.set_sensitive(self.usb_mount_point is not None)
    
    def _populate_usb_list(self):
        """Populate USB drive list"""
        # Clear existing
        while True:
            row = self.usb_list_box.get_row_at_index(0)
            if row is None:
                break
            self.usb_list_box.remove(row)
        
        # Get mounted drives
        found_drives = False
        try:
            result = subprocess.run(
                ['lsblk', '-J', '-o', 'NAME,SIZE,MOUNTPOINT,TYPE,HOTPLUG'],
                capture_output=True,
                text=True
            )
            
            print(f"lsblk output: {result.stdout}")
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                for device in data.get('blockdevices', []):
                    print(f"Device: {device.get('name')}, Type: {device.get('type')}, Hotplug: {device.get('hotplug')}")
                    
                    # Look for disk devices (not just hotplug)
                    if device.get('type') == 'disk':
                        # Check if the disk itself has a mountpoint (e.g., directly formatted USB)
                        disk_mountpoint = device.get('mountpoint')
                        if disk_mountpoint and (disk_mountpoint.startswith('/media') or disk_mountpoint.startswith('/mnt') or disk_mountpoint.startswith('/run/media')):
                            print(f"  Disk has direct mountpoint: {disk_mountpoint}")
                            self._add_usb_row(
                                device.get('name'),
                                device.get('size', 'Unknown'),
                                disk_mountpoint
                            )
                            found_drives = True
                        
                        # Also check for mounted partitions
                        for child in device.get('children', []):
                            mountpoint = child.get('mountpoint')
                            print(f"  Partition: {child.get('name')}, Mountpoint: {mountpoint}")
                            
                            # Accept any /media, /mnt, or /run/media mountpoint
                            if mountpoint and (mountpoint.startswith('/media') or mountpoint.startswith('/mnt') or mountpoint.startswith('/run/media')):
                                self._add_usb_row(
                                    child.get('name', device['name']),
                                    child.get('size', 'Unknown'),
                                    mountpoint
                                )
                                found_drives = True
                
                # If no drives found, show helpful message
                if not found_drives:
                    print("No USB drives found with mountpoints in /media, /mnt, or /run/media")
                    # Show a message in the list
                    self._show_no_drives_message()
                    
        except Exception as e:
            print(f"Error scanning USB drives: {e}")
            import traceback
            traceback.print_exc()
            self._show_no_drives_message()
        
        # Restore previously selected USB if it still exists
        if self.usb_mount_point:
            # Find and select the row with matching mountpoint
            index = 0
            while True:
                row = self.usb_list_box.get_row_at_index(index)
                if row is None:
                    break
                if hasattr(row, 'mountpoint') and Path(row.mountpoint) == self.usb_mount_point:
                    self.usb_list_box.select_row(row)
                    break
                index += 1
    
    def _show_no_drives_message(self):
        """Show message when no USB drives found"""
        row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        row_box.set_margin_start(48)
        row_box.set_margin_end(48)
        row_box.set_margin_top(24)
        row_box.set_margin_bottom(24)
        
        # Icon
        icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
        icon.set_pixel_size(48)
        icon.set_opacity(0.5)
        row_box.append(icon)
        
        # Message
        label = Gtk.Label(label="No USB drives detected")
        label.add_css_class("title-3")
        row_box.append(label)
        
        help_label = Gtk.Label()
        help_label.set_markup("<small>Please insert a USB drive and click Refresh</small>")
        help_label.add_css_class("dim-label")
        row_box.append(help_label)
        
        row = Gtk.ListBoxRow()
        row.set_child(row_box)
        row.set_selectable(False)
        row.set_activatable(False)
        
        self.usb_list_box.append(row)
    
    def _add_usb_row(self, device, size, mountpoint, is_example=False):
        """Add USB drive row to list"""
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_box.set_margin_start(12)
        row_box.set_margin_end(12)
        row_box.set_margin_top(12)
        row_box.set_margin_bottom(12)
        
        # Icon
        icon = Gtk.Image.new_from_icon_name("drive-removable-media-symbolic")
        icon.set_pixel_size(32)
        row_box.append(icon)
        
        # Info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        device_label = Gtk.Label(label=f"/dev/{device}" if not is_example else device)
        device_label.set_xalign(0)
        device_label.add_css_class("heading")
        info_box.append(device_label)
        
        details = Gtk.Label(label=f"{size} • {mountpoint}")
        details.set_xalign(0)
        details.add_css_class("caption")
        details.add_css_class("dim-label")
        info_box.append(details)
        
        row_box.append(info_box)
        
        # Store mountpoint and device in row data
        row = Gtk.ListBoxRow()
        row.set_child(row_box)
        row.mountpoint = mountpoint
        row.device = f"/dev/{device}" if not is_example else device
        
        self.usb_list_box.append(row)
    
    def _on_usb_selected(self, list_box, row):
        """Handle USB drive selection"""
        if row and hasattr(row, 'mountpoint') and hasattr(row, 'device'):
            self.usb_mount_point = Path(row.mountpoint)
            self.usb_device = row.device
            self.next_button.set_sensitive(True)
        else:
            self.next_button.set_sensitive(False)
    
    def _show_usb_preparation_page(self):
        """Show USB preparation page"""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        page_box.set_margin_start(48)
        page_box.set_margin_end(48)
        page_box.set_margin_top(48)
        page_box.set_margin_bottom(48)
        page_box.set_halign(Gtk.Align.CENTER)
        page_box.set_valign(Gtk.Align.CENTER)
        
        # Title
        title = Gtk.Label(label="Prepare USB Drive")
        title.add_css_class("title-1")
        page_box.append(title)
        
        # Warning
        warning_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        warning_box.add_css_class("card")
        warning_box.set_margin_top(12)
        warning_box.set_margin_bottom(12)
        warning_box.set_margin_start(24)
        warning_box.set_margin_end(24)
        
        warning_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
        warning_icon.set_pixel_size(48)
        warning_icon.add_css_class("warning")
        warning_icon.set_margin_start(12)
        warning_icon.set_margin_end(12)
        warning_box.append(warning_icon)
        
        warning_label = Gtk.Label()
        warning_label.set_markup("<b>⚠️ WARNING: All data on the USB drive will be erased!</b>")
        warning_label.add_css_class("title-3")
        warning_label.set_margin_start(12)
        warning_label.set_margin_end(12)
        warning_label.set_hexpand(True)
        warning_box.append(warning_label)
        
        page_box.append(warning_box)
        
        # What will happen
        info_label = Gtk.Label()
        game_name = self.game_directory.name if self.game_directory else "GAME"
        # Create safe label (max 16 chars, uppercase, no spaces)
        safe_label = game_name.upper().replace(" ", "_")[:16]
        
        info_label.set_markup(
            "<b>The USB drive will be:</b>\n\n"
            f"• Formatted as ext4\n"
            f"• Labeled as: {safe_label}\n"
            f"• Configured with proper permissions\n"
            f"• Ready for {game_name} cartridge"
        )
        info_label.set_justify(Gtk.Justification.LEFT)
        page_box.append(info_label)
        
        # Device info
        device_label = Gtk.Label()
        device_label.set_markup(f"<small>Device: {self.usb_device}</small>")
        device_label.add_css_class("dim-label")
        page_box.append(device_label)
        
        # Status label
        self.prep_status_label = Gtk.Label(label="")
        self.prep_status_label.add_css_class("dim-label")
        page_box.append(self.prep_status_label)
        
        # Prepare button
        prepare_button = Gtk.Button(label="Prepare USB Drive")
        prepare_button.add_css_class("pill")
        prepare_button.add_css_class("destructive-action")
        prepare_button.set_size_request(200, -1)
        prepare_button.set_hexpand(False)  # Don't expand horizontally
        prepare_button.set_halign(Gtk.Align.CENTER)  # Center the button
        prepare_button.connect("clicked", self._on_prepare_usb_clicked)
        page_box.append(prepare_button)
        
        self.pages.add_named(page_box, "usb_preparation")
        self.pages.set_visible_child_name("usb_preparation")
        
        # Update buttons
        self.back_button.set_visible(True)
        self.next_button.set_label("Next")
        self.next_button.set_sensitive(False)  # Enable after preparation
    
    def _on_prepare_usb_clicked(self, button):
        """Handle USB preparation button click"""
        button.set_sensitive(False)
        self.back_button.set_sensitive(False)
        
        # Run preparation in thread
        import threading
        thread = threading.Thread(target=self._prepare_usb_thread)
        thread.daemon = True
        thread.start()
    
    def _prepare_usb_thread(self):
        """Prepare USB drive (runs in background thread)"""
        try:
            from gi.repository import GLib
            
            # Step 1: Unmount
            GLib.idle_add(self.prep_status_label.set_label, "Unmounting drive...")
            result = subprocess.run(
                ['udisksctl', 'unmount', '-b', self.usb_device],
                capture_output=True,
                text=True
            )
            
            # Step 2: Format
            game_name = self.game_directory.name if self.game_directory else "GAME"
            safe_label = game_name.upper().replace(" ", "_")[:16]
            
            GLib.idle_add(self.prep_status_label.set_label, f"Formatting as ext4 with label {safe_label}...")
            
            # Use pkexec to run mkfs.ext4 with elevated privileges
            # Try different possible locations for mkfs.ext4
            mkfs_paths = ['/sbin/mkfs.ext4', '/usr/sbin/mkfs.ext4', 'mkfs.ext4']
            mkfs_cmd = None
            
            for path in mkfs_paths:
                if path == 'mkfs.ext4' or os.path.exists(path):
                    mkfs_cmd = path
                    break
            
            if not mkfs_cmd:
                raise Exception("mkfs.ext4 not found in system")
            
            format_result = subprocess.run(
                ['pkexec', mkfs_cmd, '-F', '-L', safe_label, self.usb_device],
                capture_output=True,
                text=True
            )
            
            if format_result.returncode != 0:
                error_msg = format_result.stderr or "Unknown error"
                GLib.idle_add(self._show_prep_error, f"Format failed: {error_msg}")
                return
            
            # Step 3: Mount
            GLib.idle_add(self.prep_status_label.set_label, "Mounting...")
            mount_result = subprocess.run(
                ['udisksctl', 'mount', '-b', self.usb_device],
                capture_output=True,
                text=True
            )
            
            if mount_result.returncode != 0:
                GLib.idle_add(self._show_prep_error, f"Mount failed: {mount_result.stderr}")
                return
            
            # Extract mount point from output
            # Output format: "Mounted /dev/sdb1 at /run/media/user/LABEL"
            mount_output = mount_result.stdout
            if "at" in mount_output:
                new_mount_point = mount_output.split("at")[-1].strip().rstrip('.')
                self.usb_mount_point = Path(new_mount_point)
            
            # Step 4: Set permissions
            GLib.idle_add(self.prep_status_label.set_label, "Setting permissions...")
            import os
            username = os.getenv('USER', 'phurst')
            
            # Use pkexec to change ownership
            chown_result = subprocess.run(
                ['pkexec', 'chown', '-R', f'{username}:{username}', str(self.usb_mount_point)],
                capture_output=True,
                text=True
            )
            
            if chown_result.returncode != 0:
                print(f"Warning: Could not set permissions: {chown_result.stderr}")
            
            # Success!
            GLib.idle_add(self._show_prep_success)
            
        except Exception as e:
            from gi.repository import GLib
            GLib.idle_add(self._show_prep_error, str(e))
    
    def _show_prep_success(self):
        """Show preparation success"""
        self.prep_status_label.set_markup("<b>✓ USB drive prepared successfully!</b>")
        self.next_button.set_sensitive(True)
        self.back_button.set_sensitive(True)
    
    def _show_prep_error(self, error_msg):
        """Show preparation error"""
        self.prep_status_label.set_markup(f"<b>❌ Error:</b> {error_msg}")
        self.back_button.set_sensitive(True)
    
    def _show_confirm_page(self):
        """Show confirmation page"""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        page_box.set_margin_start(48)
        page_box.set_margin_end(48)
        page_box.set_margin_top(48)
        page_box.set_margin_bottom(48)
        page_box.set_halign(Gtk.Align.CENTER)
        page_box.set_valign(Gtk.Align.CENTER)
        
        # Title
        title = Gtk.Label(label="Ready to Import")
        title.add_css_class("title-1")
        page_box.append(title)
        
        # Details
        details = Gtk.Label()
        game_name = self.game_directory.name if self.game_directory else "Unknown"
        details.set_markup(
            f"<b>Game:</b> {game_name}\n"
            f"<b>Source:</b> {self.game_directory}\n"
            f"<b>Destination:</b> {self.usb_mount_point}\n"
        )
        page_box.append(details)
        
        # Auto-launch toggle
        auto_launch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        auto_launch_label = Gtk.Label(label="Auto-launch game when cartridge is inserted")
        auto_launch_box.append(auto_launch_label)
        
        auto_launch_switch = Gtk.Switch()
        auto_launch_switch.set_active(True)
        auto_launch_switch.connect("state-set", self._on_auto_launch_toggled)
        auto_launch_box.append(auto_launch_switch)
        
        page_box.append(auto_launch_box)
        
        self.pages.add_named(page_box, "confirm")
        self.pages.set_visible_child_name("confirm")
        
        # Update buttons
        self.back_button.set_visible(True)
        self.next_button.set_label("Import")
        self.next_button.set_sensitive(True)
    
    def _on_auto_launch_toggled(self, switch, state):
        """Handle auto-launch toggle"""
        self.auto_launch = state
        return False
    
    def _show_progress_page(self):
        """Show import progress page"""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        page_box.set_margin_start(48)
        page_box.set_margin_end(48)
        page_box.set_margin_top(48)
        page_box.set_margin_bottom(48)
        page_box.set_halign(Gtk.Align.CENTER)
        page_box.set_valign(Gtk.Align.CENTER)
        
        # Title
        title = Gtk.Label(label="Importing Game...")
        title.add_css_class("title-1")
        page_box.append(title)
        
        # Spinner
        spinner = Gtk.Spinner()
        spinner.set_size_request(48, 48)
        spinner.start()
        page_box.append(spinner)
        
        # Progress label
        self.progress_label = Gtk.Label(label="Preparing...")
        self.progress_label.add_css_class("dim-label")
        page_box.append(self.progress_label)
        
        self.pages.add_named(page_box, "progress")
        self.pages.set_visible_child_name("progress")
        
        # Hide all buttons
        self.action_bar.set_visible(False)
        
        # Start import in background thread
        threading.Thread(target=self._run_import, daemon=True).start()
    
    def _run_import(self):
        """Run the import process"""
        try:
            # Call import_game.py script
            import_script = Path(__file__).parent.parent.parent / "scripts" / "import_game.py"
            
            print(f"Starting import: {self.game_directory} -> {self.usb_mount_point}")
            print(f"Import script: {import_script}")
            
            # Update progress
            GLib.idle_add(self.progress_label.set_label, "Detecting game executable...")
            
            # Run with python3 explicitly and stream output
            process = subprocess.Popen(
                ['python3', str(import_script), str(self.game_directory), str(self.usb_mount_point)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Read output line by line and update progress
            output_lines = []
            for line in process.stdout:
                line = line.strip()
                if line:
                    print(f"Import: {line}")
                    output_lines.append(line)
                    
                    # Update progress label based on output
                    if "Step 1" in line or "Detecting" in line:
                        GLib.idle_add(self.progress_label.set_label, "Detecting game files...")
                    elif "Step 2" in line or "save" in line.lower():
                        GLib.idle_add(self.progress_label.set_label, "Detecting save location...")
                    elif "Step 3" in line or "Creating" in line or "structure" in line:
                        GLib.idle_add(self.progress_label.set_label, "Creating cartridge structure...")
                    elif "Step 4" in line or "metadata" in line.lower():
                        GLib.idle_add(self.progress_label.set_label, "Generating metadata...")
                    elif "Step 5" in line or "Copying" in line:
                        GLib.idle_add(self.progress_label.set_label, "Copying game files... (this may take several minutes)")
                    elif "✓" in line or "Complete" in line:
                        GLib.idle_add(self.progress_label.set_label, "Finalizing...")
            
            # Wait for process to complete
            process.wait()
            
            if process.returncode == 0:
                # Success!
                print("Import completed successfully!")
                GLib.idle_add(self._show_success_page)
            else:
                # Error
                error_msg = "\n".join(output_lines[-10:]) if output_lines else "Unknown error"
                print(f"Import failed with code {process.returncode}")
                GLib.idle_add(self._show_error_page, error_msg)
        
        except subprocess.TimeoutExpired:
            GLib.idle_add(self._show_error_page, "Import timed out (took longer than 5 minutes)")
        except Exception as e:
            print(f"Import exception: {e}")
            import traceback
            traceback.print_exc()
            GLib.idle_add(self._show_error_page, str(e))
    
    def _show_success_page(self):
        """Show success page"""
        page = Adw.StatusPage()
        page.set_icon_name("emblem-ok-symbolic")
        page.set_title("Import Complete!")
        page.set_description(
            f"Game cartridge created successfully.\n"
            f"{'The game will auto-launch when you insert this cartridge.' if self.auto_launch else 'Auto-launch is disabled for this cartridge.'}"
        )
        
        self.pages.add_named(page, "success")
        self.pages.set_visible_child_name("success")
        
        # Show close button
        self.action_bar.set_visible(True)
        self.back_button.set_visible(False)
        self.cancel_button.set_visible(False)
        self.next_button.set_label("Done")
        self.next_button.set_sensitive(True)
        self.next_button.disconnect_by_func(self._on_next_clicked)
        self.next_button.connect("clicked", lambda *_: self.close())
    
    def _show_error_page(self, error_message):
        """Show error page"""
        page = Adw.StatusPage()
        page.set_icon_name("dialog-error-symbolic")
        page.set_title("Import Failed")
        page.set_description(f"An error occurred:\n\n{error_message}")
        
        self.pages.add_named(page, "error")
        self.pages.set_visible_child_name("error")
        
        # Show retry/close buttons
        self.action_bar.set_visible(True)
        self.back_button.set_visible(False)
        self.cancel_button.set_label("Close")
        self.next_button.set_label("Try Again")
        self.next_button.set_sensitive(True)
        self.next_button.disconnect_by_func(self._on_next_clicked)
        self.next_button.connect("clicked", lambda *_: self._show_game_selector_page())
    
    def _on_next_clicked(self, button):
        """Handle next button click"""
        current_page = self.pages.get_visible_child_name()
        
        if current_page == "welcome":
            self._show_game_selector_page()
        elif current_page == "game_selector":
            self._show_usb_selector_page()
        elif current_page == "usb_selector":
            self._show_usb_preparation_page()
        elif current_page == "usb_preparation":
            self._show_confirm_page()
        elif current_page == "confirm":
            self._show_progress_page()
    
    def _on_back_clicked(self, button):
        """Handle back button click"""
        current_page = self.pages.get_visible_child_name()
        
        if current_page == "game_selector":
            self._show_welcome_page()
        elif current_page == "usb_selector":
            self._show_game_selector_page()
        elif current_page == "usb_preparation":
            self._show_usb_selector_page()
        elif current_page == "confirm":
            self._show_usb_preparation_page()

