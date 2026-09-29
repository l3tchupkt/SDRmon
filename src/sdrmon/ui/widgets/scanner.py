"""
Scanner widgets.
"""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Label, ProgressBar

from sdrmon.scanner.models import ScanConfig, ScanResult


class ScannerWidget(Widget):
    """Displays a table of scanner results and progress."""

    DEFAULT_CSS = """
    ScannerWidget {
        width: 100%;
        height: 100%;
    }
    #scanner-config {
        height: 4;
        border: solid $accent;
        padding: 0 1;
    }
    #scanner-table {
        height: 1fr;
        border: solid $primary;
    }
    #scanner-status {
        height: 3;
        border: solid $secondary;
        padding: 0 1;
    }
    .config-label {
        width: 1fr;
    }
    """

    config: reactive[ScanConfig | None] = reactive(None)
    progress: reactive[float] = reactive(0.0)
    active_count: reactive[int] = reactive(0)
    scanned_count: reactive[int] = reactive(0)
    total_steps: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        with Vertical(id="scanner-config"):
            with Horizontal():
                yield Label("Range: N/A", id="lbl-range", classes="config-label")
                yield Label("Step: N/A", id="lbl-step", classes="config-label")
                yield Label("Dwell: N/A", id="lbl-dwell", classes="config-label")
            yield ProgressBar(id="scanner-progress", show_eta=False)

        yield DataTable(id="scanner-table")

        with Horizontal(id="scanner-status"):
            yield Label("Active: 0", id="lbl-active", classes="config-label")
            yield Label("Scanned: 0/0", id="lbl-scanned", classes="config-label")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("Frequency", "Peak (dBFS)", "Noise (dBFS)", "Status")

    def update_config(self, config: ScanConfig, total_steps: int) -> None:
        self.config = config
        self.total_steps = total_steps
        self.active_count = 0
        self.scanned_count = 0
        self.progress = 0.0

        self.query_one("#lbl-range", Label).update(
            f"Range: {config.start_frequency / 1e6:.3f} → {config.stop_frequency / 1e6:.3f} MHz"
        )
        self.query_one("#lbl-step", Label).update(f"Step: {config.step / 1e3:.0f} kHz")
        self.query_one("#lbl-dwell", Label).update(
            f"Dwell: {config.dwell_time * 1000:.0f} ms"
        )

        pb = self.query_one(ProgressBar)
        pb.total = total_steps
        pb.progress = 0

        table = self.query_one(DataTable)
        table.clear()

    def add_result(self, result: ScanResult) -> None:
        table = self.query_one(DataTable)

        freq_str = f"{result.frequency / 1e6:.3f} MHz"
        peak_str = f"{result.peak_power:.1f}"
        noise_str = f"{result.noise_floor:.1f}"

        if result.occupied:
            status_text = Text("ACTIVE", style="red bold")
            self.active_count += 1
        else:
            status_text = Text("idle", style="dim")

        table.add_row(freq_str, peak_str, noise_str, status_text)

        # Auto-scroll to the bottom
        table.move_cursor(row=table.row_count - 1)

        self.scanned_count += 1
        self.progress = self.scanned_count

        pb = self.query_one(ProgressBar)
        pb.advance(1)

        self.query_one("#lbl-active", Label).update(f"Active: {self.active_count}")
        self.query_one("#lbl-scanned", Label).update(
            f"Scanned: {self.scanned_count}/{self.total_steps}"
        )
