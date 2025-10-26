"""Main application entry point for Physica GTK"""

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, Gdk
from pathlib import Path

from physica_gtk.window import PhysicaWindow


class PhysicaApplication(Adw.Application):
    """Main Physica GTK application class"""
    
    def __init__(self):
        super().__init__(application_id='org.physicaapp.Desktop',
                         flags=0)
        self.window = None
    
    def do_activate(self):
        """Called when the application is activated"""
        # Create window if it doesn't exist
        if not self.window:
            self.window = PhysicaWindow(application=self)
        
        # Present window (bring to front)
        self.window.present()
    
    def do_startup(self):
        """Called once at application startup"""
        Adw.Application.do_startup(self)
        
        # Load custom CSS
        self._load_css()
        
        # Set up application-wide actions
        self._setup_actions()
    
    def _load_css(self):
        """Load custom CSS stylesheet"""
        css_provider = Gtk.CssProvider()
        css_path = Path(__file__).parent / "style.css"
        
        if css_path.exists():
            css_provider.load_from_path(str(css_path))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            print(f"✓ Loaded custom CSS from {css_path}")
        else:
            print(f"⚠ CSS file not found: {css_path}")
    
    def _setup_actions(self):
        """Set up application-wide actions"""
        # Quit action (Ctrl+Q)
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<primary>q"])
        
        # Refresh action (Ctrl+R)
        refresh_action = Gio.SimpleAction.new("refresh", None)
        refresh_action.connect("activate", self._on_refresh)
        self.add_action(refresh_action)
        self.set_accels_for_action("app.refresh", ["<primary>r", "F5"])
    
    def _on_refresh(self, action, param):
        """Handle refresh action"""
        if self.window:
            self.window.refresh_cartridges()


def main():
    """Main entry point"""
    app = PhysicaApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())

