#include "sdrmon/backends/rtl_sdr/rtl_sdr_loader.hpp"
#include <iostream>

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace sdrmon {
namespace backends {

RtlSdrLoader::~RtlSdrLoader() {
    if (handle_) {
#ifdef _WIN32
        FreeLibrary(static_cast<HMODULE>(handle_));
#else
        dlclose(handle_);
#endif
    }
}

bool RtlSdrLoader::load() {
    if (loaded_) return true;

#ifdef _WIN32
    // On Windows, the DLL might be rtlsdr.dll or librtlsdr.dll
    if (load_from("rtlsdr.dll")) return true;
    if (load_from("librtlsdr.dll")) return true;
    
    // Also try the bin directory next to python executable or current dir
    if (load_from("bin/rtlsdr.dll")) return true;
#else
    if (load_from("librtlsdr.so")) return true;
    if (load_from("librtlsdr.so.0")) return true;
    if (load_from("librtlsdr.dylib")) return true; // MacOS
#endif

    return false;
}

bool RtlSdrLoader::load_from(const std::string& path) {
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
    api_.get_device_count = reinterpret_cast<decltype(api_.get_device_count)>(get_sym("rtlsdr_get_device_count"));
    api_.get_device_name = reinterpret_cast<decltype(api_.get_device_name)>(get_sym("rtlsdr_get_device_name"));
    api_.get_device_usb_strings = reinterpret_cast<decltype(api_.get_device_usb_strings)>(get_sym("rtlsdr_get_device_usb_strings"));
    api_.open = reinterpret_cast<decltype(api_.open)>(get_sym("rtlsdr_open"));
    api_.close = reinterpret_cast<decltype(api_.close)>(get_sym("rtlsdr_close"));
    api_.set_center_freq = reinterpret_cast<decltype(api_.set_center_freq)>(get_sym("rtlsdr_set_center_freq"));
    api_.get_center_freq = reinterpret_cast<decltype(api_.get_center_freq)>(get_sym("rtlsdr_get_center_freq"));
    api_.set_sample_rate = reinterpret_cast<decltype(api_.set_sample_rate)>(get_sym("rtlsdr_set_sample_rate"));
    api_.get_sample_rate = reinterpret_cast<decltype(api_.get_sample_rate)>(get_sym("rtlsdr_get_sample_rate"));
    api_.set_tuner_gain = reinterpret_cast<decltype(api_.set_tuner_gain)>(get_sym("rtlsdr_set_tuner_gain"));
    api_.get_tuner_gains = reinterpret_cast<decltype(api_.get_tuner_gains)>(get_sym("rtlsdr_get_tuner_gains"));
    api_.set_tuner_gain_mode = reinterpret_cast<decltype(api_.set_tuner_gain_mode)>(get_sym("rtlsdr_set_tuner_gain_mode"));
    api_.set_agc_mode = reinterpret_cast<decltype(api_.set_agc_mode)>(get_sym("rtlsdr_set_agc_mode"));
    api_.set_tuner_bandwidth = reinterpret_cast<decltype(api_.set_tuner_bandwidth)>(get_sym("rtlsdr_set_tuner_bandwidth"));
    api_.reset_buffer = reinterpret_cast<decltype(api_.reset_buffer)>(get_sym("rtlsdr_reset_buffer"));
    api_.read_sync = reinterpret_cast<decltype(api_.read_sync)>(get_sym("rtlsdr_read_sync"));

    // Check minimum required symbols
    if (!api_.get_device_count || !api_.open || !api_.close || !api_.read_sync) {
        // Missing core functions
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
