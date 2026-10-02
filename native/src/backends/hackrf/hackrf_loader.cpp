#include "sdrmon/backends/hackrf/hackrf_loader.hpp"
#include <iostream>

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace sdrmon {
namespace backends {

HackRFLoader::~HackRFLoader() {
    if (handle_) {
#ifdef _WIN32
        FreeLibrary(static_cast<HMODULE>(handle_));
#else
        dlclose(handle_);
#endif
    }
}

bool HackRFLoader::load() {
    if (loaded_) return true;

#ifdef _WIN32
    if (load_from("hackrf.dll")) return true;
    if (load_from("libhackrf.dll")) return true;
    if (load_from("bin/hackrf.dll")) return true;
#else
    if (load_from("libhackrf.so")) return true;
    if (load_from("libhackrf.so.0")) return true;
    if (load_from("libhackrf.dylib")) return true; // MacOS
    if (load_from("libhackrf.0.dylib")) return true; 
#endif

    return false;
}

bool HackRFLoader::load_from(const std::string& path) {
    if (loaded_) return true;

#ifdef _WIN32
    HMODULE handle = LoadLibraryA(path.c_str());
    if (!handle) return false;
    
    auto get_sym = [handle](const char* name) -> void* {
        return reinterpret_cast<void*>(GetProcAddress(handle, name));
    };
#else
    void* handle = dlopen(path.c_str(), RTLD_NOW | RTLD_LOCAL);
    if (!handle) return false;
    
    auto get_sym = [handle](const char* name) -> void* {
        return dlsym(handle, name);
    };
#endif

    // Resolve symbols
    api_.hackrf_init = reinterpret_cast<decltype(api_.hackrf_init)>(get_sym("hackrf_init"));
    api_.hackrf_exit = reinterpret_cast<decltype(api_.hackrf_exit)>(get_sym("hackrf_exit"));
    api_.hackrf_device_list = reinterpret_cast<decltype(api_.hackrf_device_list)>(get_sym("hackrf_device_list"));
    api_.hackrf_device_list_free = reinterpret_cast<decltype(api_.hackrf_device_list_free)>(get_sym("hackrf_device_list_free"));
    api_.hackrf_open = reinterpret_cast<decltype(api_.hackrf_open)>(get_sym("hackrf_open"));
    api_.hackrf_open_by_serial = reinterpret_cast<decltype(api_.hackrf_open_by_serial)>(get_sym("hackrf_open_by_serial"));
    api_.hackrf_close = reinterpret_cast<decltype(api_.hackrf_close)>(get_sym("hackrf_close"));
    api_.hackrf_start_rx = reinterpret_cast<decltype(api_.hackrf_start_rx)>(get_sym("hackrf_start_rx"));
    api_.hackrf_stop_rx = reinterpret_cast<decltype(api_.hackrf_stop_rx)>(get_sym("hackrf_stop_rx"));
    api_.hackrf_set_freq = reinterpret_cast<decltype(api_.hackrf_set_freq)>(get_sym("hackrf_set_freq"));
    api_.hackrf_set_sample_rate = reinterpret_cast<decltype(api_.hackrf_set_sample_rate)>(get_sym("hackrf_set_sample_rate"));
    api_.hackrf_set_amp_enable = reinterpret_cast<decltype(api_.hackrf_set_amp_enable)>(get_sym("hackrf_set_amp_enable"));
    api_.hackrf_set_lna_gain = reinterpret_cast<decltype(api_.hackrf_set_lna_gain)>(get_sym("hackrf_set_lna_gain"));
    api_.hackrf_set_vga_gain = reinterpret_cast<decltype(api_.hackrf_set_vga_gain)>(get_sym("hackrf_set_vga_gain"));
    api_.hackrf_set_baseband_filter_bandwidth = reinterpret_cast<decltype(api_.hackrf_set_baseband_filter_bandwidth)>(get_sym("hackrf_set_baseband_filter_bandwidth"));

    // Check minimum required symbols
    if (!api_.hackrf_init || !api_.hackrf_open || !api_.hackrf_close || !api_.hackrf_start_rx || !api_.hackrf_stop_rx) {
#ifdef _WIN32
        FreeLibrary(handle);
#else
        dlclose(handle);
#endif
        return false;
    }

    handle_ = handle;
    loaded_ = true;
    return true;
}

} // namespace backends
} // namespace sdrmon
