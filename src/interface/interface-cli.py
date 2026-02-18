"""
Minimal Textual-based CLI interface.
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class PopupScreen(ModalScreen[None]):
    """Small popup shown from the main interface."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Popup opened", id="popup-message"),
            Button("Close", id="close-popup"),
            id="popup-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle popup button actions."""
        if event.button.id == "close-popup":
            self.close_popup_action()

    def close_popup_action(self) -> None:
        """Close the popup."""
        self.dismiss()


class TestInterfaceApp(App[None]):
    """Simple class-based terminal interface with two actions."""

    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        width: 40;
        height: auto;
        border: round $accent;
        padding: 1 2;
        align: center middle;
    }

    #title {
        text-style: bold;
        content-align: center middle;
        margin-bottom: 1;
    }

    #button-row {
        width: 100%;
        height: auto;
        align-horizontal: center;
    }

    Button {
        margin: 0 1;
        min-width: 14;
    }

    #status {
        content-align: center middle;
        margin-top: 1;
    }

    #popup-container {
        width: 32;
        height: auto;
        border: round $warning;
        background: $panel;
        padding: 1;
    }

    #popup-message {
        content-align: center middle;
        margin-bottom: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._refresh_count = 0

    def compose(self) -> ComposeResult:
        """Build the interface layout."""
        yield Vertical(
            Static("Test Interface", id="title"),
            Horizontal(
                Button("Open Popup", id="open-popup"),
                Button("Refresh CLI", id="refresh-cli"),
                id="button-row",
            ),
            Static("Ready", id="status"),
            id="main-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dispatch button actions to dedicated functions."""
        button_id = event.button.id
        if button_id == "open-popup":
            self.open_popup_action()
        elif button_id == "refresh-cli":
            self.refresh_cli_action()

    def open_popup_action(self) -> None:
        """Open a popup screen."""
        self.push_screen(PopupScreen())

    def refresh_cli_action(self) -> None:
        """Refresh the interface from the refresh button."""
        self.update_interface()

    def _update_core_state(self) -> None:
        """Internal update logic for app state."""
        self._refresh_count += 1

    def _sync_status_view(self) -> None:
        """Apply internal state to visible widgets."""
        status = self.query_one("#status", Static)
        status.update(f"Refreshed: {self._refresh_count}")

    def update_interface(self) -> None:
        """
        Public update function, callable from outside.

        Internal core functionality updates are performed privately.
        """
        self._update_core_state()
        if not self.is_mounted:
            return

        self._sync_status_view()
        self.refresh(repaint=True, layout=True)


def update_interface(app: TestInterfaceApp) -> None:
    """External helper to trigger the app update function."""
    app.update_interface()


def run_interface() -> None:
    """Module entrypoint to run the minimal interface."""
    TestInterfaceApp().run()


if __name__ == "__main__":
    run_interface()
