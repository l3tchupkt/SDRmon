#include "sdrmon/backends/pluto/pluto_loader.hpp"
#include <iostream>

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace sdrmon {
namespace backends {

PlutoLoader::~PlutoLoader() {
    if (handle_) {
#ifdef _WIN32
        FreeLibrary(static_cast<HMODULE>(handle_));
#else
        dlclose(handle_);
#endif
    }
}

bool PlutoLoader::load() {
    if (loaded_) return true;

#ifdef _WIN32
    if (load_from("libiio.dll")) return true;
    if (load_from("bin/libiio.dll")) return true;
#else
    if (load_from("libiio.so")) return true;
    if (load_from("libiio.so.0")) return true;
    if (load_from("libiio.dylib")) return true; 
    if (load_from("libiio.0.dylib")) return true; 
#endif

    return false;
}

bool PlutoLoader::load_from(const std::string& path) {
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
    api_.iio_create_default_context = reinterpret_cast<decltype(api_.iio_create_default_context)>(get_sym("iio_create_default_context"));
    api_.iio_create_network_context = reinterpret_cast<decltype(api_.iio_create_network_context)>(get_sym("iio_create_network_context"));
    api_.iio_context_destroy = reinterpret_cast<decltype(api_.iio_context_destroy)>(get_sym("iio_context_destroy"));
    api_.iio_context_get_devices_count = reinterpret_cast<decltype(api_.iio_context_get_devices_count)>(get_sym("iio_context_get_devices_count"));
    api_.iio_context_get_device = reinterpret_cast<decltype(api_.iio_context_get_device)>(get_sym("iio_context_get_device"));
    api_.iio_device_get_name = reinterpret_cast<decltype(api_.iio_device_get_name)>(get_sym("iio_device_get_name"));
    api_.iio_device_get_id = reinterpret_cast<decltype(api_.iio_device_get_id)>(get_sym("iio_device_get_id"));
    api_.iio_device_find_channel = reinterpret_cast<decltype(api_.iio_device_find_channel)>(get_sym("iio_device_find_channel"));
    api_.iio_channel_attr_write_longlong = reinterpret_cast<decltype(api_.iio_channel_attr_write_longlong)>(get_sym("iio_channel_attr_write_longlong"));
    api_.iio_channel_attr_write_double = reinterpret_cast<decltype(api_.iio_channel_attr_write_double)>(get_sym("iio_channel_attr_write_double"));
    api_.iio_channel_enable = reinterpret_cast<decltype(api_.iio_channel_enable)>(get_sym("iio_channel_enable"));
    api_.iio_channel_disable = reinterpret_cast<decltype(api_.iio_channel_disable)>(get_sym("iio_channel_disable"));
    api_.iio_device_create_buffer = reinterpret_cast<decltype(api_.iio_device_create_buffer)>(get_sym("iio_device_create_buffer"));
    api_.iio_buffer_destroy = reinterpret_cast<decltype(api_.iio_buffer_destroy)>(get_sym("iio_buffer_destroy"));
    api_.iio_buffer_refill = reinterpret_cast<decltype(api_.iio_buffer_refill)>(get_sym("iio_buffer_refill"));
    api_.iio_buffer_first = reinterpret_cast<decltype(api_.iio_buffer_first)>(get_sym("iio_buffer_first"));
    api_.iio_buffer_end = reinterpret_cast<decltype(api_.iio_buffer_end)>(get_sym("iio_buffer_end"));
    api_.iio_buffer_step = reinterpret_cast<decltype(api_.iio_buffer_step)>(get_sym("iio_buffer_step"));

    // Basic required functions
    if (!api_.iio_context_destroy || !api_.iio_device_get_name || !api_.iio_device_create_buffer) {
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
