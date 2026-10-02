from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Input, Select, Static

from sdrmon.ui.widgets.slider import Slider, SliderChanged


class FrequencyControl(Widget):
    DEFAULT_CSS = """
    FrequencyControl {
        height: auto;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        padding: 0 1;
        layout: vertical;
    }
    .freq-row {
        layout: horizontal;
        height: 1;
        align: center middle;
        margin-bottom: 1;
    }
    .freq-slider-row {
        layout: horizontal;
        height: 1;
        margin-bottom: 1;
    }
    .freq-btn {
        min-width: 5;
        height: 1;
        border: none;
        background: #1565c0;
        color: #eceff1;
        margin: 0 1;
    }
    .freq-btn:hover { background: #1e88e5; }
    .freq-btn:focus { text-style: bold; background: #1976d2; }

    #freq-input {
        width: 18;
        height: 1;
        border: none;
        background: #131920;
        text-align: center;
    }
    #freq-label-min, #freq-label-max {
        color: #b0bec5;
        width: 12;
    }
    #freq-label-max { text-align: right; }
    FrequencyControl > Slider { width: 1fr; margin: 0 1; }
    """

    frequency = reactive(100_000_000)
    min_freq = reactive(24_000_000)
    max_freq = reactive(1766_000_000)

    def compose(self) -> ComposeResult:
        self.border_title = "FREQUENCY"
        with Horizontal(classes="freq-slider-row"):
            yield Static("24.000 MHz", id="freq-label-min")
            yield Slider(
                min_value=24.0, max_value=1766.0, value=100.0, id="freq-slider"
            )
            yield Static("1766.000 MHz", id="freq-label-max")
        with Horizontal(classes="freq-row"):
            yield Button("−", id="freq-dec", classes="freq-btn")
            yield Input("100.000 MHz", id="freq-input")
            yield Button("+", id="freq-inc", classes="freq-btn")

    def watch_min_freq(self, value: int) -> None:
        try:
            self.query_one("#freq-label-min", Static).update(f"{value / 1e6:.3f} MHz")
            self.query_one("#freq-slider", Slider).min_value = value / 1e6
        except Exception:
            pass

    def watch_max_freq(self, value: int) -> None:
        try:
            self.query_one("#freq-label-max", Static).update(f"{value / 1e6:.3f} MHz")
            self.query_one("#freq-slider", Slider).max_value = value / 1e6
        except Exception:
            pass

    def watch_frequency(self, value: int) -> None:
        try:
            self.query_one("#freq-input", Input).value = f"{value / 1e6:.3f} MHz"
            self.query_one("#freq-slider", Slider).value = value / 1e6
        except Exception:
            pass

    def on_slider_changed(self, event: SliderChanged) -> None:
        if event.slider.id == "freq-slider":
            new_freq = int(event.value * 1e6)
            # Post message to parent screen
            from sdrmon.ui.widgets.spectrum import SpectrumClick

            self.post_message(SpectrumClick(new_freq))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from sdrmon.ui.widgets.spectrum import SpectrumClick

        if event.button.id == "freq-dec":
            self.post_message(SpectrumClick(self.frequency - 100_000))
        elif event.button.id == "freq-inc":
            self.post_message(SpectrumClick(self.frequency + 100_000))


class GainChanged(Message):
    def __init__(self, gain: float) -> None:
        super().__init__()
        self.gain = gain


class GainControl(Widget):
    DEFAULT_CSS = """
    GainControl {
        height: auto;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        padding: 0 1;
        layout: horizontal;
        align: left middle;
    }
    GainControl > Slider { width: 1fr; margin: 0 1; }
    #gain-value { width: 8; text-align: right; color: #b0bec5; }
    """
    gain = reactive(40.0)

    def compose(self) -> ComposeResult:
        self.border_title = "GAIN"
        yield Slider(min_value=0.0, max_value=60.0, value=40.0, id="gain-slider")
        yield Static("40.0 dB", id="gain-value")

    def watch_gain(self, value: float) -> None:
        try:
            self.query_one("#gain-slider", Slider).value = value
            self.query_one("#gain-value", Static).update(f"{value:.1f} dB")
        except Exception:
            pass

    def on_slider_changed(self, event: SliderChanged) -> None:
        if event.slider.id == "gain-slider":
            self.post_message(GainChanged(event.value))


class RateChanged(Message):
    def __init__(self, rate: int) -> None:
        super().__init__()
        self.rate = rate


class RateControl(Widget):
    DEFAULT_CSS = """
    RateControl {
        height: auto;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        padding: 0 1;
        layout: horizontal;
        align: center middle;
    }
    RateControl > Select {
        width: 1fr;
        height: 1;
        border: none;
        background: #131920;
    }
    """

    rate = reactive(2000000)

    def set_supported_rates(self, rates: list[int]) -> None:
        opts = []
        for r in rates:
            opts.append((f"{r / 1e6:.3f} MS/s", r))

        sel = self.query_one("#rate-select", Select)
        sel.set_options(opts)

    def watch_rate(self, value: int) -> None:
        try:
            sel = self.query_one("#rate-select", Select)
            sel.value = value
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        self.border_title = "RATE"
        yield Select(
            [
                ("1.000 MS/s", 1000000),
                ("2.000 MS/s", 2000000),
                ("2.400 MS/s", 2400000),
                ("3.200 MS/s", 3200000),
            ],
            id="rate-select",
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "rate-select" and event.value != Select.BLANK:
            try:
                self.post_message(RateChanged(int(str(event.value))))
            except (ValueError, TypeError):
                pass


class AudioSettingsChanged(Message):
    def __init__(
        self,
        mode: str | None = None,
        bw: int | None = None,
        squelch: float | None = None,
        volume: float | None = None,
        muted: bool | None = None,
        device: str | None = None,
    ) -> None:
        super().__init__()
        self.mode = mode
        self.bw = bw
        self.squelch = squelch
        self.volume = volume
        self.muted = muted
        self.device = device


class AudioControl(Widget):
    DEFAULT_CSS = """
    AudioControl {
        height: auto;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        padding: 0 1;
        layout: vertical;
    }
    .audio-row {
        layout: horizontal;
        height: 1;
        margin-bottom: 1;
        align: left middle;
    }
    .audio-label { width: 10; color: #b0bec5; }
    AudioControl > Horizontal > Select { height: 1; width: 1fr; border: none; background: #131920; }
    AudioControl > Horizontal > Slider { width: 1fr; margin: 0 1; }
    AudioControl > Horizontal > Checkbox { height: 1; border: none; }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "AUDIO & DEMOD"
        with Horizontal(classes="audio-row"):
            yield Static("Mode/BW:", classes="audio-label")
            yield Select(
                [("NFM", "nfm"), ("FM", "fm"), ("WFM", "wfm"), ("AM", "am")],
                id="audio-mode",
                value="nfm",
            )
            yield Select(
                [("12.5k", 12500), ("200k", 200000), ("10k", 10000)],
                id="audio-bw",
                value=12500,
            )
        with Horizontal(classes="audio-row"):
            yield Static("Squelch:", classes="audio-label")
            yield Slider(min_value=-100, max_value=0, value=-50, id="squelch-slider")
        with Horizontal(classes="audio-row"):
            yield Static("Volume:", classes="audio-label")
            yield Slider(min_value=0, max_value=100, value=50, id="vol-slider")
        with Horizontal(classes="audio-row"):
            yield Static("Out/Mute:", classes="audio-label")
            yield Select(
                [("Default", "default"), ("Null", "null")],
                id="audio-device",
                value="default",
            )
            yield Checkbox("Mute", id="audio-mute")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        if event.select.id == "audio-mode":
            self.post_message(AudioSettingsChanged(mode=str(event.value)))
        elif event.select.id == "audio-bw":
            try:
                self.post_message(AudioSettingsChanged(bw=int(str(event.value))))
            except (ValueError, TypeError):
                pass
        elif event.select.id == "audio-device":
            self.post_message(AudioSettingsChanged(device=str(event.value)))

    def on_slider_changed(self, event: SliderChanged) -> None:
        if event.slider.id == "squelch-slider":
            self.post_message(AudioSettingsChanged(squelch=event.value))
        elif event.slider.id == "vol-slider":
            self.post_message(AudioSettingsChanged(volume=event.value / 100.0))

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "audio-mute":
            self.post_message(AudioSettingsChanged(muted=event.value))


class ZoomScaleControl(Widget):
    DEFAULT_CSS = """
    ZoomScaleControl {
        height: auto;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        padding: 0 1;
        layout: vertical;
    }
    .z-row {
        layout: horizontal;
        height: 1;
        margin-bottom: 1;
        align: left middle;
    }
    .z-label { width: 12; color: #b0bec5; }
    .z-btn {
        min-width: 5;
        height: 1;
        border: none;
        background: #1565c0;
        color: #eceff1;
        margin: 0 1;
    }
    .z-btn:hover { background: #1e88e5; }
    .z-btn:focus { text-style: bold; background: #1976d2; }
    .z-val { width: 8; text-align: center; }
    #sc-auto { width: 1fr; }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "ZOOM & SCALE"
        with Horizontal(classes="z-row"):
            yield Static("Spectrum Z:", classes="z-label")
            yield Button("−", id="sz-dec", classes="z-btn")
            yield Static("1.0x", id="sz-val", classes="z-val")
            yield Button("+", id="sz-inc", classes="z-btn")
        with Horizontal(classes="z-row"):
            yield Static("Waterfall Z:", classes="z-label")
            yield Button("−", id="wz-dec", classes="z-btn")
            yield Static("1.0x", id="wz-val", classes="z-val")
            yield Button("+", id="wz-inc", classes="z-btn")
        with Horizontal(classes="z-row"):
            yield Static("Scale:", classes="z-label")
            yield Button("−", id="sc-dec", classes="z-btn")
            yield Static("40 dB", id="sc-val", classes="z-val")
            yield Button("+", id="sc-inc", classes="z-btn")
        with Horizontal(classes="z-row"):
            yield Static("", classes="z-label")
            yield Button("AUTO", id="sc-auto", classes="z-btn")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        action_map = {
            "sz-dec": "zoom_out",
            "sz-inc": "zoom_in",
            "wz-dec": "zoom_out",
            "wz-inc": "zoom_in",
            "sc-dec": "scale_down",
            "sc-inc": "scale_up",
            "sc-auto": "auto_scale",
        }
        if event.button.id in action_map:
            # For zoom, we have to make sure focus goes to the correct widget
            if event.button.id in ("sz-dec", "sz-inc"):
                self.app.screen.query_one("#spectrum").focus()
            elif event.button.id in ("wz-dec", "wz-inc"):
                self.app.screen.query_one("#waterfall").focus()
            await self.app.screen.run_action(action_map[event.button.id])


class DeviceControl(Widget):
    DEFAULT_CSS = """
    DeviceControl {
        height: auto;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        padding: 0 1;
        layout: vertical;
    }
    .dev-row {
        layout: horizontal;
        height: 1;
    }
    .dev-label { color: #b0bec5; width: 10; }
    .dev-val { color: #ffffff; width: 1fr; }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "DEVICE & STATUS"
        with Horizontal(classes="dev-row"):
            yield Static("Device:", classes="dev-label")
            yield Static("...", id="dev-name", classes="dev-val")
        with Horizontal(classes="dev-row"):
            yield Static("Status:", classes="dev-label")
            yield Static("...", id="dev-status", classes="dev-val")
        with Horizontal(classes="dev-row"):
            yield Static("Center:", classes="dev-label")
            yield Static("...", id="dev-center", classes="dev-val")
        with Horizontal(classes="dev-row"):
            yield Static("Channel:", classes="dev-label")
            yield Static("...", id="dev-channel", classes="dev-val")
        with Horizontal(classes="dev-row"):
            yield Static("Rate:", classes="dev-label")
            yield Static("...", id="dev-rate", classes="dev-val")
        with Horizontal(classes="dev-row"):
            yield Static("Peak:", classes="dev-label")
            yield Static("...", id="dev-peak", classes="dev-val")


class ActionButtons(Widget):
    DEFAULT_CSS = """
    ActionButtons {
        height: auto;
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 2;
        padding: 1 1;
    }
    .action-btn {
        width: 100%;
        height: 3;
        background: #1565c0;
        border: none;
    }
    .action-btn:hover { background: #1e88e5; }
    """

    def compose(self) -> ComposeResult:
        yield Button("Device", id="btn-device_select", classes="action-btn")
        yield Button("Capture", id="btn-capture", classes="action-btn")
        yield Button("Scan", id="btn-scan", classes="action-btn")
        yield Button("Pause", id="btn-toggle_pause", classes="action-btn")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("btn-"):
            action = event.button.id[4:]
            await self.app.screen.run_action(action)
