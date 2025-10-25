"""Main application window - Memory Card Manager"""

from gi.repository import Gtk, Adw, GLib, Gio
from physica_gtk.dbus_client import PhysicaDBusClient
from physica_gtk.game_card import GameCard, FormatNewCard
from physica_gtk.import_wizard import ImportWizardDialog


class PhysicaWindow(Adw.ApplicationWindow):
    """Main application window"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.set_title("Physica")
        self.set_default_size(900, 700)
        
        # D-Bus client
        self.dbus = PhysicaDBusClient()
        
        # Game cards dict (uuid -> GameCard widget)
        self.game_cards = {}
        
        self._build_ui()
        self._load_games()
        self._connect_signals()
    
    def _build_ui(self):
        """Build the main UI"""
        # Header bar
        header = Adw.HeaderBar()
        
        # Refresh button
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh game library")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        header.pack_end(refresh_button)
        
        # Main content
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)
        
        # Toast overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        toolbar_view.set_content(self.toast_overlay)
        
        # Scrolled window for game grid
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='x-large' weight='bold'>Game Library</span>")
        title_label.set_xalign(0)
        title_label.set_margin_bottom(12)
        main_box.append(title_label)
        
        # Stats bar
        self.stats_label = Gtk.Label()
        self.stats_label.set_xalign(0)
        self.stats_label.add_css_class("dim-label")
        self.stats_label.set_margin_bottom(24)
        main_box.append(self.stats_label)
        
        # Game grid (FlowBox)
        self.game_grid = Gtk.FlowBox()
        self.game_grid.set_valign(Gtk.Align.START)
        self.game_grid.set_max_children_per_line(30)
        self.game_grid.set_min_children_per_line(1)  # Allow single item per row
        self.game_grid.set_row_spacing(24)
        self.game_grid.set_column_spacing(24)
        self.game_grid.set_homogeneous(False)  # Don't make items homogeneous to prevent stretching
        self.game_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        main_box.append(self.game_grid)
        
        # Empty state
        self.empty_state = Adw.StatusPage()
        self.empty_state.set_icon_name("drive-removable-media-symbolic")
        self.empty_state.set_title("No Games Yet")
        self.empty_state.set_description("Import your first game cartridge to get started")
        
        # Create a container to control button size
        button_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_container.set_halign(Gtk.Align.CENTER)
        button_container.set_hexpand(False)
        
        empty_button = Gtk.Button(label="Import Game")
        empty_button.add_css_class("pill")
        empty_button.add_css_class("suggested-action")
        empty_button.add_css_class("import-game-button")  # Add CSS class for size constraint
        empty_button.set_size_request(200, -1)  # Set fixed width
        empty_button.set_hexpand(False)  # Don't expand horizontally
        empty_button.connect("clicked", self._on_import_clicked)
        
        button_container.append(empty_button)
        self.empty_state.set_child(button_container)
        
        # Stack to switch between grid and empty state
        self.stack = Gtk.Stack()
        self.stack.add_named(main_box, "grid")
        self.stack.add_named(self.empty_state, "empty")
        
        scrolled.set_child(self.stack)
        self.toast_overlay.set_child(scrolled)
        
        self.set_content(toolbar_view)
    
    def _load_games(self):
        """Load games from registry and populate grid"""
        # Clear existing cards
        self.game_cards.clear()
        child = self.game_grid.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.game_grid.remove(child)
            child = next_child
        
        # Get all games from registry
        games = self.dbus.get_all_games()
        
        if not games:
            self.stack.set_visible_child_name("empty")
            self._update_stats(0, 0)
            return
        
        self.stack.set_visible_child_name("grid")
        
        # Create card for each game
        for game in games:
            card = GameCard(game)
            self.game_cards[game["uuid"]] = card
            
            # Connect launch button
            card.launch_button.connect("clicked", self._on_launch_game, game["uuid"])
            
            # Setup context menu actions
            self._setup_card_actions(card, game["uuid"])
            
            self.game_grid.append(card)
        
        # Add "Format New" card at the end
        format_card = FormatNewCard(self._on_import_clicked)
        self.game_grid.append(format_card)
        
        # Update stats
        stats = self.dbus.get_registry_stats()
        self._update_stats(
            stats.get("total_games", len(games)),
            stats.get("total_playtime", 0)
        )
    
    def _update_stats(self, total_games: int, total_playtime: int):
        """Update the stats label
        
        Args:
            total_games: Total number of games
            total_playtime: Total playtime in seconds
        """
        hours = total_playtime // 3600
        minutes = (total_playtime % 3600) // 60
        
        if total_games == 0:
            self.stats_label.set_label("")
        elif total_games == 1:
            self.stats_label.set_label(f"1 game • {hours}h {minutes}m played")
        else:
            self.stats_label.set_label(f"{total_games} games • {hours}h {minutes}m played")
    
    def _connect_signals(self):
        """Connect to D-Bus signals"""
        if not self.dbus.is_connected():
            return
        
        self.dbus.connect_cartridge_inserted(self._on_cartridge_inserted)
        self.dbus.connect_cartridge_removed(self._on_cartridge_removed)
        self.dbus.connect_game_launched(self._on_game_launched)
        self.dbus.connect_game_stopped(self._on_game_stopped)
    
    def _show_toast(self, message: str):
        """Show a toast notification
        
        Args:
            message: Message to display
        """
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)  # 3 seconds
        self.toast_overlay.add_toast(toast)
    
    def _setup_card_actions(self, card: GameCard, uuid: str):
        """Setup context menu actions for a game card
        
        Args:
            card: The GameCard widget
            uuid: Game UUID
        """
        # Create action group for this card
        action_group = Gio.SimpleActionGroup()
        
        # Launch action
        launch_action = Gio.SimpleAction.new("launch", None)
        launch_action.connect("activate", lambda *_: self._on_context_launch(uuid))
        action_group.add_action(launch_action)
        
        # Details action
        details_action = Gio.SimpleAction.new("details", None)
        details_action.connect("activate", lambda *_: self._on_context_details(uuid))
        action_group.add_action(details_action)
        
        # Location action
        location_action = Gio.SimpleAction.new("location", None)
        location_action.connect("activate", lambda *_: self._on_context_location(uuid))
        action_group.add_action(location_action)
        
        # Remove action
        remove_action = Gio.SimpleAction.new("remove", None)
        remove_action.connect("activate", lambda *_: self._on_context_remove(uuid))
        action_group.add_action(remove_action)
        
        # Insert action group into card
        card.insert_action_group("card", action_group)
    
    # ========== Action Handlers ==========
    
    def _on_launch_game(self, button, uuid: str):
        """Handle launch button click
        
        Args:
            button: Button that was clicked
            uuid: Game UUID to launch
        """
        card = self.game_cards.get(uuid)
        if not card:
            return
        
        game_name = card.game_data.get("game_name", "Game")
        
        # Disable button and show launching state
        button.set_sensitive(False)
        button.set_label("Launching...")
        
        # Launch game via D-Bus
        success = self.dbus.launch_game(uuid)
        
        if success:
            self._show_toast(f"🚀 Launching {game_name}...")
        else:
            self._show_toast(f"❌ Failed to launch {game_name}")
            # Re-enable button on failure
            button.set_sensitive(True)
            button.set_label("Launch")
    
    # ========== Context Menu Handlers ==========
    
    def _on_context_launch(self, uuid: str):
        """Handle launch from context menu"""
        card = self.game_cards.get(uuid)
        if card and card.launch_button.get_visible():
            self._on_launch_game(card.launch_button, uuid)
    
    def _on_context_details(self, uuid: str):
        """Handle view details from context menu"""
        card = self.game_cards.get(uuid)
        if not card:
            return
        
        # TODO: Show details dialog (implement in next step)
        self._show_toast(f"📊 Details for {card.game_data.get('game_name')} (coming soon)")
    
    def _on_context_location(self, uuid: str):
        """Handle open location from context menu"""
        card = self.game_cards.get(uuid)
        if not card:
            return
        
        mount_point = card.game_data.get("last_mount_point")
        if not mount_point:
            self._show_toast("❌ Cartridge location not available")
            return
        
        # Open file manager at mount point
        import subprocess
        try:
            subprocess.Popen(["xdg-open", mount_point])
            self._show_toast(f"📂 Opening {mount_point}")
        except Exception as e:
            self._show_toast(f"❌ Failed to open location: {e}")
    
    def _on_context_remove(self, uuid: str):
        """Handle remove from library from context menu"""
        card = self.game_cards.get(uuid)
        if not card:
            return
        
        game_name = card.game_data.get("game_name", "this game")
        
        # Show confirmation dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(f"Remove {game_name}?")
        dialog.set_body("This will remove the game from your library. The cartridge files will not be deleted.")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("remove", "Remove")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        def on_response(dialog, response):
            if response == "remove":
                # Remove from registry via D-Bus
                success = self.dbus.remove_from_registry(uuid)
                if success:
                    self._show_toast(f"🗑️ Removed {game_name} from library")
                    # Remove card from UI
                    if uuid in self.game_cards:
                        self.game_grid.remove(card)
                        del self.game_cards[uuid]
                    # Update stats
                    stats = self.dbus.get_registry_stats()
                    self._update_stats(
                        stats.get("total_games", 0),
                        stats.get("total_playtime", 0)
                    )
                else:
                    self._show_toast(f"❌ Failed to remove {game_name}")
        
        dialog.connect("response", on_response)
        dialog.present()
    
    # ========== Signal Handlers ==========
    
    def _on_cartridge_inserted(self, uuid: str, name: str):
        """Handle cartridge inserted signal"""
        print(f"Cartridge inserted: {name} ({uuid})")
        
        # Show toast
        GLib.idle_add(self._show_toast, f"📀 {name} inserted")
        
        # If card exists, update its state
        if uuid in self.game_cards:
            GLib.idle_add(self.game_cards[uuid].set_inserted, True)
        else:
            # New cartridge, reload grid
            GLib.idle_add(self._load_games)
    
    def _on_cartridge_removed(self, uuid: str):
        """Handle cartridge removed signal"""
        print(f"Cartridge removed: {uuid}")
        
        # Get game name for toast
        game_name = "Cartridge"
        if uuid in self.game_cards:
            game_name = self.game_cards[uuid].game_data.get("game_name", "Cartridge")
            GLib.idle_add(self.game_cards[uuid].set_inserted, False)
        
        # Show toast
        GLib.idle_add(self._show_toast, f"📤 {game_name} removed")
    
    def _on_game_launched(self, uuid: str, name: str):
        """Handle game launched signal"""
        print(f"Game launched: {name} ({uuid})")
        
        # Show toast
        GLib.idle_add(self._show_toast, f"▶️ {name} is now running")
        
        if uuid in self.game_cards:
            GLib.idle_add(self.game_cards[uuid].set_running, True)
    
    def _on_game_stopped(self, uuid: str, name: str, playtime: int):
        """Handle game stopped signal"""
        print(f"Game stopped: {name}, played {playtime}s")
        
        # Format playtime for toast
        minutes = playtime // 60
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if hours > 0:
            time_str = f"{hours}h {remaining_minutes}m"
        else:
            time_str = f"{minutes}m"
        
        # Show toast
        GLib.idle_add(self._show_toast, f"⏸️ {name} stopped (played {time_str})")
        
        if uuid in self.game_cards:
            # Update playtime
            games = self.dbus.get_all_games()
            for game in games:
                if game["uuid"] == uuid:
                    GLib.idle_add(self.game_cards[uuid].update_playtime, game["total_playtime"])
                    break
            
            GLib.idle_add(self.game_cards[uuid].set_running, False)
        
        # Update stats
        stats = self.dbus.get_registry_stats()
        GLib.idle_add(
            self._update_stats,
            stats.get("total_games", 0),
            stats.get("total_playtime", 0)
        )
    
    def _on_refresh_clicked(self, button):
        """Handle refresh button click"""
        self.dbus.refresh_cartridges()
        self._load_games()
    
    def _on_import_clicked(self, *args):
        """Handle import button click"""
        wizard = ImportWizardDialog(self)
        wizard.present()
    
    def refresh_cartridges(self):
        """Public method for refreshing cartridges (called by app-level action)"""
        self._on_refresh_clicked(None)
