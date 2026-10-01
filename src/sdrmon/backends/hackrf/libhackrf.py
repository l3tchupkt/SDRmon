import sys
from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    c_byte,
    c_char_p,
    c_double,
    c_int,
    c_uint8,
    c_uint32,
    c_uint64,
    c_void_p,
    cdll,
)

HACKRF_ERROR_OK = 0
HACKRF_ERROR_INVALID_PARAM = -2
HACKRF_ERROR_NOT_FOUND = -5
HACKRF_ERROR_BUSY = -6
HACKRF_ERROR_NO_MEM = -11
HACKRF_ERROR_LIBUSB = -1000
HACKRF_ERROR_THREAD = -1001
HACKRF_ERROR_STREAMING_THREAD_ERR = -1002
HACKRF_ERROR_STREAMING_STOPPED = -1003
HACKRF_ERROR_STREAMING_EXIT_CALLED = -1004
HACKRF_ERROR_USB_API_VERSION = -1005
HACKRF_ERROR_NOT_LAST_DEVICE = -2000
HACKRF_ERROR_OTHER = -9999

p_hackrf_device = c_void_p


class hackrf_transfer(Structure):
    _fields_ = [
        ("device", p_hackrf_device),
        ("buffer", POINTER(c_byte)),
        ("buffer_length", c_int),
        ("valid_length", c_int),
        ("rx_ctx", c_void_p),
        ("tx_ctx", c_void_p),
    ]


class read_partid_serialno_t(Structure):
    _fields_ = [
        ("part_id", c_uint32 * 2),
        ("serial_no", c_uint32 * 4),
    ]


class hackrf_device_list_t(Structure):
    _fields_ = [
        ("serial_numbers", POINTER(c_char_p)),
        ("usb_board_ids", c_void_p),
        ("usb_device_index", POINTER(c_int)),
        ("devicecount", c_int),
        ("usb_devices", POINTER(c_void_p)),
        ("usb_devicecount", c_int),
    ]


def load_libhackrf():
    if sys.platform == "win32":
        names = ["hackrf.dll", "libhackrf.dll"]
    elif sys.platform == "darwin":
        names = ["libhackrf.dylib", "libhackrf.0.dylib"]
    else:
        names = ["libhackrf.so", "libhackrf.so.0"]

    for name in names:
        try:
            lib = cdll.LoadLibrary(name)
            return lib
        except OSError:
            continue

    # Fallback for Linux where it might be installed in standard paths but not in LD_LIBRARY_PATH
    if sys.platform != "win32" and sys.platform != "darwin":
        try:
            return cdll.LoadLibrary("libhackrf.so.0")
        except OSError:
            pass

    return None


libhackrf = load_libhackrf()

if libhackrf:
    libhackrf.hackrf_init.restype = c_int
    libhackrf.hackrf_init.argtypes = []

    libhackrf.hackrf_exit.restype = c_int
    libhackrf.hackrf_exit.argtypes = []

    libhackrf.hackrf_device_list.restype = POINTER(hackrf_device_list_t)
    libhackrf.hackrf_device_list.argtypes = []

    libhackrf.hackrf_device_list_free.restype = None
    libhackrf.hackrf_device_list_free.argtypes = [POINTER(hackrf_device_list_t)]

    libhackrf.hackrf_device_list_open.restype = c_int
    libhackrf.hackrf_device_list_open.argtypes = [
        POINTER(hackrf_device_list_t),
        c_int,
        POINTER(p_hackrf_device),
    ]

    libhackrf.hackrf_open.restype = c_int
    libhackrf.hackrf_open.argtypes = [POINTER(p_hackrf_device)]

    libhackrf.hackrf_open_by_serial.restype = c_int
    libhackrf.hackrf_open_by_serial.argtypes = [c_char_p, POINTER(p_hackrf_device)]

    libhackrf.hackrf_close.restype = c_int
    libhackrf.hackrf_close.argtypes = [p_hackrf_device]

    libhackrf.hackrf_start_rx.restype = c_int
    libhackrf.hackrf_start_rx.argtypes = [
        p_hackrf_device,
        CFUNCTYPE(c_int, POINTER(hackrf_transfer)),
        c_void_p,
    ]

    libhackrf.hackrf_stop_rx.restype = c_int
    libhackrf.hackrf_stop_rx.argtypes = [p_hackrf_device]

    libhackrf.hackrf_set_freq.restype = c_int
    libhackrf.hackrf_set_freq.argtypes = [p_hackrf_device, c_uint64]

    libhackrf.hackrf_set_sample_rate.restype = c_int
    libhackrf.hackrf_set_sample_rate.argtypes = [p_hackrf_device, c_double]

    libhackrf.hackrf_set_amp_enable.restype = c_int
    libhackrf.hackrf_set_amp_enable.argtypes = [p_hackrf_device, c_uint8]

    libhackrf.hackrf_set_lna_gain.restype = c_int
    libhackrf.hackrf_set_lna_gain.argtypes = [p_hackrf_device, c_uint32]

    libhackrf.hackrf_set_vga_gain.restype = c_int
    libhackrf.hackrf_set_vga_gain.argtypes = [p_hackrf_device, c_uint32]

    libhackrf.hackrf_set_baseband_filter_bandwidth.restype = c_int
    libhackrf.hackrf_set_baseband_filter_bandwidth.argtypes = [p_hackrf_device, c_uint32]

    libhackrf.hackrf_board_partid_serialno_read.restype = c_int
    libhackrf.hackrf_board_partid_serialno_read.argtypes = [
        p_hackrf_device,
        POINTER(read_partid_serialno_t),
    ]

    libhackrf.hackrf_board_id_name.restype = c_char_p
    libhackrf.hackrf_board_id_name.argtypes = [c_int]

    libhackrf.hackrf_version_string_read.restype = c_int
    libhackrf.hackrf_version_string_read.argtypes = [p_hackrf_device, c_char_p, c_uint8]
