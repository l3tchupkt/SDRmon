"""
SDRmon Terminal Application Theme.

Centralized CSS and style constants for the full-screen TUI.
"""

# ---------------------------------------------------------------------------
# Shared CSS injected into SDRmonApp.CSS
# ---------------------------------------------------------------------------

SDRMON_CSS = """
/* ── Palette ────────────────────────────────────────────────────────────── */
$sdr-bg:        #0a0e14;
$sdr-surface:   #131920;
$sdr-panel:     #1a2332;
$sdr-border:    #1e88e5;
$sdr-border2:   #0d47a1;
$sdr-accent:    #00b0ff;
$sdr-green:     #00e676;
$sdr-yellow:    #ffea00;
$sdr-red:       #ff1744;
$sdr-orange:    #ff6d00;
$sdr-muted:     #546e7a;
$sdr-text:      #eceff1;
$sdr-text2:     #b0bec5;

/* ── App root ───────────────────────────────────────────────────────────── */
Screen {
    background: $sdr-bg;
    color: $sdr-text;
}

/* ── Header ─────────────────────────────────────────────────────────────── */
#sdr-header {
    height: 1;
    background: $sdr-border2;
    color: $sdr-text;
    padding: 0 1;
    layout: horizontal;
    content-align: left middle;
}
#sdr-header-left {
    width: 1fr;
    content-align: left middle;
}
#sdr-header-right {
    width: auto;
    content-align: right middle;
}

/* ── Footer / shortcuts bar ─────────────────────────────────────────────── */
#sdr-footer {
    height: 2;
    background: $sdr-border2;
    color: $sdr-text2;
    padding: 0 1;
    layout: horizontal;
    content-align: left middle;
}

/* ── Status indicator pills ─────────────────────────────────────────────── */
.pill-running {
    color: $sdr-green;
}
.pill-paused {
    color: $sdr-yellow;
}
.pill-error {
    color: $sdr-red;
}
.pill-recording {
    color: $sdr-orange;
}
.pill-replay {
    color: $sdr-accent;
}
.pill-idle {
    color: $sdr-muted;
}

/* ── Panel borders ───────────────────────────────────────────────────────── */
.sdr-panel {
    border: solid $sdr-border;
    background: $sdr-surface;
}
.sdr-panel-title {
    color: $sdr-accent;
    text-style: bold;
}

/* ── Device list (startup screen) ───────────────────────────────────────── */
DeviceListItem {
    height: 5;
    border: solid $sdr-border2;
    background: $sdr-surface;
    padding: 0 1;
    margin-bottom: 1;
}
DeviceListItem:focus {
    border: solid $sdr-accent;
    background: $sdr-panel;
}
DeviceListItem.selected {
    border: solid $sdr-accent;
    background: $sdr-panel;
}
DeviceListItem > .device-name {
    text-style: bold;
    color: $sdr-text;
}
DeviceListItem > .device-sub {
    color: $sdr-text2;
}

/* ── Modals ──────────────────────────────────────────────────────────────── */
SDRmonModal {
    align: center middle;
    background: $sdr-bg 70%;
}
.modal-dialog {
    width: 56;
    height: auto;
    border: solid $sdr-accent;
    background: $sdr-panel;
    padding: 1 2;
}
.modal-title {
    text-style: bold;
    color: $sdr-accent;
    margin-bottom: 1;
}
.modal-footer {
    height: 1;
    margin-top: 1;
    color: $sdr-text2;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
SDRmonButton {
    height: 1;
    min-width: 12;
    background: $sdr-border2;
    color: $sdr-text;
    border: none;
    margin: 0 1 0 0;
}
SDRmonButton:hover {
    background: $sdr-border;
    color: $sdr-text;
}
SDRmonButton:focus {
    border: solid $sdr-accent;
    background: $sdr-border;
}
SDRmonButton.primary {
    background: $sdr-accent;
    color: $sdr-bg;
}
SDRmonButton.danger {
    background: $sdr-red;
    color: $sdr-text;
}
SDRmonButton.success {
    background: $sdr-green;
    color: $sdr-bg;
}

/* ── Select list ─────────────────────────────────────────────────────────── */
SDRmonSelect {
    height: auto;
    max-height: 20;
    overflow-y: auto;
}
.select-item {
    height: 1;
    padding: 0 1;
    color: $sdr-text2;
}
.select-item:focus {
    background: $sdr-border;
    color: $sdr-text;
}
.select-item.active {
    color: $sdr-accent;
    text-style: bold;
}

/* ── Input ───────────────────────────────────────────────────────────────── */
Input {
    background: $sdr-bg;
    color: $sdr-text;
    border: solid $sdr-border2;
}
Input:focus {
    border: solid $sdr-accent;
}

/* ── Spectrum + Waterfall widgets ────────────────────────────────────────── */
SpectrumWidget {
    height: 1fr;
    border: solid $sdr-border2;
    background: $sdr-bg;
}
WaterfallWidget {
    height: 1fr;
    border: solid $sdr-border2;
    background: $sdr-bg;
}

/* ── Scanner table ───────────────────────────────────────────────────────── */
ScannerWidget {
    height: 1fr;
    border: solid $sdr-border2;
    background: $sdr-surface;
}

/* ── Event log ───────────────────────────────────────────────────────────── */
EventLog {
    height: 6;
    border: solid $sdr-border2;
    background: $sdr-bg;
    overflow-y: auto;
    padding: 0 1;
}

/* ── Hidden helper ───────────────────────────────────────────────────────── */
.hidden {
    display: none;
}
"""
