"""
SDRmon Textual Application.

The main application shell. Handles:
- Screen management (startup → monitor → scanner → modals)
- Global quit
- Replay file browser
- Cross-screen wiring
"""

from __future__ import annotations

from typing import Any

from textual.app import App

from sdrmon.core.device import SDRDevice
from sdrmon.ui.theme import SDRMON_CSS


class SDRmonApp(App[Any]):
    """
    SDRmon full-screen terminal application.

    Starts with the device selector (StartupScreen) unless a device is
    provided directly (for CLI compatibility).
    """

    CSS = SDRMON_CSS

    def __init__(self, device: SDRDevice | None = None) -> None:
        super().__init__()
        self._initial_device = device
        from sdrmon.core.config import SDRmonConfig

        self.sdrmon_config = SDRmonConfig.load()
        self.dark = self.sdrmon_config.dark_mode

    def on_mount(self) -> None:
        if self._initial_device is not None:
            # CLI compatibility: skip startup screen
            self._start_monitor(self._initial_device)
        else:
            from sdrmon.ui.screens.startup import StartupScreen

            self.push_screen(StartupScreen())

    def switch_to_monitor(self, device: SDRDevice) -> None:
        """Switch from startup/any screen to the live monitor screen."""
        from sdrmon.ui.screens.monitor import MonitorScreen

        self.pop_screen()  # remove startup
        self.push_screen(MonitorScreen(device))

    def _start_monitor(self, device: SDRDevice) -> None:
        """Push the monitor screen (used when device is passed directly)."""
        from sdrmon.ui.screens.monitor import MonitorScreen

        self.push_screen(MonitorScreen(device))

    def switch_to_startup(self) -> None:
        """Return to the startup screen, discarding the current screen."""
        from sdrmon.ui.screens.startup import StartupScreen

        # Pop all screens until we're at the base, then push startup
        while len(self.screen_stack) > 1:
            try:
                self.pop_screen()
            except Exception:
                break
        self.push_screen(StartupScreen())

    def open_replay_browser(self) -> None:
        """Open a file picker modal for replay, then navigate to monitor."""
        from sdrmon.ui.screens.replay_browser import ReplayModal

        def on_result(device: SDRDevice | None) -> None:
            if device:
                self.switch_to_monitor(device)

        self.push_screen(ReplayModal(), on_result)

    def action_quit(self) -> None:
        """Save config on quit."""
        try:
            self.sdrmon_config.save()
        except Exception:
            pass
        super().action_quit()


def start_tui(device: SDRDevice | None = None) -> None:
    """Launch the SDRmon terminal application."""
    app = SDRmonApp(device)
    app.run()
