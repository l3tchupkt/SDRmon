import sys
import platform
import importlib.util

def check_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None

def setup_parser(parser):
    pass

def run(args):
    print("SDRmon Doctor\n")
    
    # Python
    py_version = platform.python_version()
    print(f"Python        {'[OK]  ' if sys.version_info >= (3, 10) else '[FAIL]'} {py_version}")
    
    # Native Core
    try:
        import sdrmon_native # type: ignore
        print("Native Core   [OK]")
        native_ok = True
    except ImportError as e:
        print(f"Native Core   [FAIL] ({e})")
        native_ok = False
        
    # TUI
    tui_ok = check_module("textual") and check_module("rich")
    print(f"TUI           {'[OK]' if tui_ok else '[FAIL]'}")
    
    # DSP
    dsp_ok = check_module("numpy") and check_module("scipy")
    print(f"DSP           {'[OK]' if dsp_ok else '[FAIL]'}")
    
    # Audio
    audio_ok = check_module("sounddevice")
    print(f"Audio         {'[OK]' if audio_ok else '[FAIL]'}")
    
    # SDR Backends
    if native_ok:
        from sdrmon.native.manager import NativeSDRManager
        mgr = NativeSDRManager()
        try:
            devices = mgr.discover()
            rtlsdr = [d for d in devices if d.driver == "rtlsdr"]
            if rtlsdr:
                print(f"RTL-SDR       [OK] {rtlsdr[0].product}")
            else:
                print("RTL-SDR       -")
        except Exception:
            print("RTL-SDR       - (discovery failed)")
    else:
        print("RTL-SDR       -")
        
    print("HackRF        -")
    print("PlutoSDR      -")
    
    print("\nTroubleshooting:")
    if not native_ok:
        print("- Native module failed to load. Ensure you installed the correct wheel for your architecture.")
        print("- On Windows, ensure Visual C++ Redistributable is installed.")
        print("- If you built from source, ensure CMake built the module successfully.")
        sys.exit(1)
        
    if not tui_ok:
        print("- TUI dependencies missing. Run `pip install sdrmon[tui]`")
    if not audio_ok:
        print("- Audio dependencies missing. Run `pip install sdrmon[audio]`")
    if not dsp_ok:
        print("- DSP dependencies missing. Run `pip install sdrmon[dsp]`")
    
    if not any([not native_ok, not tui_ok, not audio_ok, not dsp_ok]):
        print("- All core components are healthy.")
