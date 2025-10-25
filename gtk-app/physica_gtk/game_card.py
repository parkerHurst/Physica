"""Game card widget for memory card manager UI"""

from gi.repository import Gtk, Adw, GLib, Gio, Gdk
from datetime import datetime


class GameCard(Gtk.Box):
    """A card representing a game in the memory card manager"""
    
    def __init__(self, game_data: dict):
        """Initialize game card
        
        Args:
            game_data: Dictionary with game info from registry
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.game_data = game_data
        self.uuid = game_data.get("uuid", "")
        self.is_running = False
        
        # Card styling
        self.add_css_class("card")
        self.add_css_class("game-card")
        self.set_size_request(200, 160)  # Reduced height without icon area
        
        # Status styling
        if game_data.get("is_inserted"):
            self.add_css_class("card-inserted")
        else:
            self.add_css_class("card-offline")
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the card UI"""
        # Info area (icon/cover removed for early access)
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_margin_start(12)
        info_box.set_margin_end(12)
        info_box.set_margin_top(12)
        info_box.set_margin_bottom(12)
        
        # Game name
        name_label = Gtk.Label(label=self.game_data.get("game_name", "Unknown"))
        name_label.set_wrap(True)
        name_label.set_max_width_chars(20)
        name_label.set_xalign(0.5)
        name_label.add_css_class("title-4")
        info_box.append(name_label)
        
        # Playtime
        playtime_text = self._format_playtime(self.game_data.get("total_playtime", 0))
        self.playtime_label = Gtk.Label(label=playtime_text)
        self.playtime_label.set_xalign(0.5)
        self.playtime_label.add_css_class("caption")
        info_box.append(self.playtime_label)
        
        # Last played
        last_played = self.game_data.get("last_played", "")
        if last_played:
            last_played_text = self._format_last_played(last_played)
            last_played_label = Gtk.Label(label=last_played_text)
            last_played_label.set_xalign(0.5)
            last_played_label.add_css_class("caption")
            last_played_label.add_css_class("dim-label")
            info_box.append(last_played_label)
        
        # Status indicator
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0.5)
        self.status_label.add_css_class("caption")
        self._update_status_label()
        info_box.append(self.status_label)
        
        # Launch button (only show if inserted and not running)
        self.launch_button = Gtk.Button(label="Launch")
        self.launch_button.add_css_class("pill")
        self.launch_button.add_css_class("suggested-action")
        self.launch_button.set_margin_top(8)
        self.launch_button.set_visible(False)  # Hidden by default
        info_box.append(self.launch_button)
        
        self.append(info_box)
        
        # Update button visibility
        self._update_button_visibility()
        
        # Setup context menu (right-click)
        self._setup_context_menu()
    
    def _format_playtime(self, seconds: int) -> str:
        """Format playtime in a friendly way
        
        Args:
            seconds: Total playtime in seconds
            
        Returns:
            Formatted string like "12h 34m" or "Never played"
        """
        if seconds == 0:
            return "Never played"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _format_last_played(self, iso_date: str) -> str:
        """Format last played date
        
        Args:
            iso_date: ISO format date string
            
        Returns:
            Formatted string like "Oct 24" or "Today"
        """
        try:
            date = datetime.fromisoformat(iso_date)
            today = datetime.now()
            
            if date.date() == today.date():
                return "Last played today"
            elif (today - date).days == 1:
                return "Last played yesterday"
            else:
                return f"Last: {date.strftime('%b %d')}"
        except:
            return ""
    
    def _update_status_label(self):
        """Update the status label based on current state"""
        if self.is_running:
            self.status_label.set_markup("<b>▶ RUNNING</b>")
            self.status_label.remove_css_class("success")
            self.status_label.add_css_class("accent")
        elif self.game_data.get("is_inserted"):
            self.status_label.set_markup("<b>● READY</b>")
            self.status_label.remove_css_class("accent")
            self.status_label.add_css_class("success")
        else:
            self.status_label.set_label("")
            self.status_label.remove_css_class("accent")
            self.status_label.remove_css_class("success")
    
    def _update_button_visibility(self):
        """Update launch button visibility based on state"""
        # Show button if: inserted AND not running
        should_show = self.game_data.get("is_inserted") and not self.is_running
        self.launch_button.set_visible(should_show)
        
        # Reset button state when making it visible again
        if should_show:
            self.launch_button.set_sensitive(True)
            self.launch_button.set_label("Launch")
    
    def _setup_context_menu(self):
        """Setup right-click context menu"""
        # Create menu model
        menu = Gio.Menu()
        
        # Launch action (if inserted and not running)
        if self.game_data.get("is_inserted") and not self.is_running:
            menu.append("Launch Game", f"card.launch")
        
        # View details
        menu.append("View Details", f"card.details")
        
        # Open location (if inserted)
        if self.game_data.get("is_inserted"):
            menu.append("Open Cartridge Location", f"card.location")
        
        # Remove from library
        menu.append("Remove from Library", f"card.remove")
        
        # Create popover menu
        self.popover_menu = Gtk.PopoverMenu()
        self.popover_menu.set_menu_model(menu)
        self.popover_menu.set_parent(self)
        self.popover_menu.set_has_arrow(False)
        
        # Setup right-click gesture
        gesture = Gtk.GestureClick()
        gesture.set_button(3)  # Right mouse button
        gesture.connect("released", self._on_right_click)
        self.add_controller(gesture)
        
        # Store callbacks (to be connected by parent window)
        self.on_launch_callback = None
        self.on_details_callback = None
        self.on_location_callback = None
        self.on_remove_callback = None
    
    def _on_right_click(self, gesture, n_press, x, y):
        """Handle right-click to show context menu"""
        # Update menu based on current state
        self._update_context_menu()
        
        # Position and show popover
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        self.popover_menu.set_pointing_to(rect)
        self.popover_menu.popup()
    
    def _update_context_menu(self):
        """Update context menu based on current state"""
        # Recreate menu with current state
        menu = Gio.Menu()
        
        # Launch action (if inserted and not running)
        if self.game_data.get("is_inserted") and not self.is_running:
            menu.append("Launch Game", f"card.launch")
        
        # View details
        menu.append("View Details", f"card.details")
        
        # Open location (if inserted)
        if self.game_data.get("is_inserted"):
            menu.append("Open Cartridge Location", f"card.location")
        
        # Remove from library
        menu.append("Remove from Library", f"card.remove")
        
        self.popover_menu.set_menu_model(menu)
    
    def set_running(self, is_running: bool):
        """Update card to show running state
        
        Args:
            is_running: Whether game is currently running
        """
        self.is_running = is_running
        self._update_status_label()
        self._update_button_visibility()
        
        if is_running:
            self.add_css_class("card-running")
        else:
            self.remove_css_class("card-running")
    
    def set_inserted(self, is_inserted: bool):
        """Update card to show inserted state
        
        Args:
            is_inserted: Whether cartridge is currently inserted
        """
        self.game_data["is_inserted"] = is_inserted
        
        if is_inserted:
            self.add_css_class("card-inserted")
            self.remove_css_class("card-offline")
        else:
            self.remove_css_class("card-inserted")
            self.add_css_class("card-offline")
        
        self._update_status_label()
        self._update_button_visibility()
    
    def update_playtime(self, seconds: int):
        """Update the displayed playtime
        
        Args:
            seconds: New total playtime in seconds
        """
        self.game_data["total_playtime"] = seconds
        self.playtime_label.set_label(self._format_playtime(seconds))


class FormatNewCard(Gtk.Box):
    """Special card for creating new cartridges"""
    
    def __init__(self, on_click_callback):
        """Initialize format new card
        
        Args:
            on_click_callback: Function to call when clicked
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.callback = on_click_callback
        
        # Card styling
        self.add_css_class("card")
        self.add_css_class("format-new-card")
        self.set_size_request(200, 160)  # Reduced height to match game cards
        self.set_hexpand(False)  # Don't expand horizontally
        self.set_vexpand(False)  # Don't expand vertically
        
        # Make it clickable
        gesture = Gtk.GestureClick()
        gesture.connect("released", lambda *_: self.callback())
        self.add_controller(gesture)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the card UI"""
        # Info area (icon removed for early access)
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        info_box.set_margin_start(12)
        info_box.set_margin_end(12)
        info_box.set_margin_top(24)
        info_box.set_margin_bottom(24)
        info_box.set_halign(Gtk.Align.CENTER)
        info_box.set_valign(Gtk.Align.CENTER)
        
        # Plus symbol (text-based)
        plus_label = Gtk.Label()
        plus_label.set_markup("<span size='x-large' weight='bold'>+</span>")
        plus_label.add_css_class("dim-label")
        info_box.append(plus_label)
        
        # Text
        name_label = Gtk.Label(label="Format New\nCartridge")
        name_label.set_justify(Gtk.Justification.CENTER)
        name_label.add_css_class("title-4")
        info_box.append(name_label)
        
        desc_label = Gtk.Label(label="Import a game")
        desc_label.add_css_class("caption")
        desc_label.add_css_class("dim-label")
        info_box.append(desc_label)
        
        self.append(info_box)

