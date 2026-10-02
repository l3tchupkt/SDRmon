from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, DataTable, Label

from sdrmon.dsp.channel import Channel
from sdrmon.dsp.detector import SignalCandidate


class SignalSelected(Message):
    def __init__(self, frequency: float, bandwidth: float):
        super().__init__()
        self.frequency = frequency
        self.bandwidth = bandwidth


class CreateChannelMsg(Message):
    def __init__(self, frequency: float, bandwidth: float, mode: str):
        super().__init__()
        self.frequency = frequency
        self.bandwidth = bandwidth
        self.mode = mode


class SignalPanel(Vertical):
    DEFAULT_CSS = """
    SignalPanel {
        height: auto;
        min-height: 10;
        max-height: 15;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        background: #060a10;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "DETECTED SIGNALS"
        dt = DataTable(id="signal-table", cursor_type="row")
        dt.add_columns("Freq (MHz)", "Power", "BW (kHz)", "Mode")
        yield dt

    def update_signals(self, signals: list[SignalCandidate]):
        dt = self.query_one(DataTable)
        dt.clear()
        from sdrmon.dsp.detector import suggest_mode

        for s in signals:
            mode = suggest_mode(s.bandwidth)
            dt.add_row(
                f"{s.frequency / 1e6:.3f}",
                f"{s.power:.1f} dB",
                f"{s.bandwidth / 1000:.1f}",
                mode,
                key=str(s.frequency),
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # User clicked a row, let's parse it
        row = event.data_table.get_row(event.row_key)
        freq_mhz = float(row[0])
        bw_khz = float(row[2])
        mode = row[3]
        self.post_message(CreateChannelMsg(freq_mhz * 1e6, bw_khz * 1000, mode))


class ChannelItem(Horizontal):
    DEFAULT_CSS = """
    ChannelItem {
        height: 3;
        border-bottom: solid #1e3a5c;
        padding: 0 1;
    }
    .ch-info { width: 1fr; }
    .ch-controls { width: auto; layout: horizontal; }
    """

    def __init__(self, channel: Channel):
        super().__init__()
        self.channel = channel

    def compose(self) -> ComposeResult:
        with Vertical(classes="ch-info"):
            yield Label(
                f"CH{self.channel.channel_id} {self.channel.frequency / 1e6:.3f} MHz {self.channel.mode}"
            )
            yield Label(f"Sq: {self.channel.squelch:.0f} dB")
        with Horizontal(classes="ch-controls"):
            yield Button(
                "M",
                id=f"mute-{self.channel.channel_id}",
                variant="error" if self.channel.muted else "primary",
            )
            yield Button("X", id=f"rm-{self.channel.channel_id}", variant="error")


class RemoveChannelMsg(Message):
    def __init__(self, channel_id: int):
        super().__init__()
        self.channel_id = channel_id


class MuteChannelMsg(Message):
    def __init__(self, channel_id: int):
        super().__init__()
        self.channel_id = channel_id


class ChannelPanel(VerticalScroll):
    DEFAULT_CSS = """
    ChannelPanel {
        height: auto;
        min-height: 5;
        max-height: 15;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        background: #060a10;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "CHANNELS"
        yield Vertical(id="channel-list")

    def update_channels(self, channels: list[Channel]):
        clist = self.query_one("#channel-list", Vertical)
        clist.remove_children()
        for ch in channels:
            clist.mount(ChannelItem(ch))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id:
            if event.button.id.startswith("mute-"):
                ch_id = int(event.button.id.split("-")[1])
                self.post_message(MuteChannelMsg(ch_id))
            elif event.button.id.startswith("rm-"):
                ch_id = int(event.button.id.split("-")[1])
                self.post_message(RemoveChannelMsg(ch_id))
