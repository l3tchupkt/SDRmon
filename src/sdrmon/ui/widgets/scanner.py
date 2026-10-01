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
        layout: vertical;
    }
    #scanner-config {
        height: 4;
        background: #131920;
        border-bottom: solid #1e88e5;
        padding: 0 1;
    }
    .cfg-col {
        width: 1fr;
        height: 2;
    }
    .cfg-title {
        color: #546e7a;
        text-style: bold;
    }
    .cfg-val {
        color: #eceff1;
    }
    #scanner-progress {
        height: 1;
        margin-top: 1;
    }
    #scanner-table {
        height: 1fr;
        border: none;
        background: #060a10;
    }
    #scanner-status {
        height: 1;
        background: #131920;
        padding: 0 1;
        color: #b0bec5;
    }
    .status-label {
        width: auto;
        margin-right: 4;
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
                with Vertical(classes="cfg-col"):
                    yield Label("START", classes="cfg-title")
                    yield Label("N/A", id="lbl-start", classes="cfg-val")
                with Vertical(classes="cfg-col"):
                    yield Label("STOP", classes="cfg-title")
                    yield Label("N/A", id="lbl-stop", classes="cfg-val")
                with Vertical(classes="cfg-col"):
                    yield Label("STEP", classes="cfg-title")
                    yield Label("N/A", id="lbl-step", classes="cfg-val")
                with Vertical(classes="cfg-col"):
                    yield Label("DWELL", classes="cfg-title")
                    yield Label("N/A", id="lbl-dwell", classes="cfg-val")
            yield ProgressBar(id="scanner-progress", show_eta=False)

        yield DataTable(id="scanner-table")

        with Horizontal(id="scanner-status"):
            yield Label("Active: 0", id="lbl-active", classes="status-label")
            yield Label("Scanned: 0/0", id="lbl-scanned", classes="status-label")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("FREQUENCY", "PEAK", "NOISE", "DELTA", "STATUS")

    def update_config(self, config: ScanConfig, total_steps: int) -> None:
        self.config = config
        self.total_steps = total_steps
        self.active_count = 0
        self.scanned_count = 0
        self.progress = 0.0

        self.query_one("#lbl-start", Label).update(
            f"{config.start_frequency / 1e6:.3f} MHz"
        )
        self.query_one("#lbl-stop", Label).update(
            f"{config.stop_frequency / 1e6:.3f} MHz"
        )
        self.query_one("#lbl-step", Label).update(f"{config.step / 1e3:.0f} kHz")
        self.query_one("#lbl-dwell", Label).update(f"{config.dwell_time * 1000:.0f} ms")

        pb = self.query_one(ProgressBar)
        pb.total = total_steps
        pb.progress = 0

        table = self.query_one(DataTable)
        table.clear()

    def add_result(self, result: ScanResult) -> None:
        table = self.query_one(DataTable)

        freq_str = f"{result.frequency / 1e6:.3f} MHz"
        peak_str = f"{result.peak_power:.1f} dB"
        noise_str = f"{result.noise_floor:.1f} dB"
        delta_str = f"{result.peak_power - result.noise_floor:.1f} dB"

        if result.occupied:
            status_text = Text("OCCUPIED", style="red bold")
            self.active_count += 1
        else:
            status_text = Text("-", style="dim")

        table.add_row(freq_str, peak_str, noise_str, delta_str, status_text)

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

    def clear_results(self) -> None:
        """Reset the scanner table and progress."""
        self.active_count = 0
        self.scanned_count = 0
        self.progress = 0.0
        table = self.query_one(DataTable)
        table.clear()
        pb = self.query_one(ProgressBar)
        pb.progress = 0
        self.query_one("#lbl-active", Label).update("Active: 0")
        self.query_one("#lbl-scanned", Label).update("Scanned: 0/0")
