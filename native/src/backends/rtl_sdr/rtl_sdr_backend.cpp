#include "sdrmon/backends/rtl_sdr/rtl_sdr_backend.hpp"
#include "sdrmon/backends/rtl_sdr/rtl_sdr_device.hpp"
#include "sdrmon/core/errors.hpp"
#include <iostream>

namespace sdrmon {
namespace backends {

RtlSdrBackend::RtlSdrBackend() : loader_(RtlSdrLoader::get()) {
    loader_.load(); // Attempt to load
}

std::string RtlSdrBackend::name() const {
    return "rtl_sdr";
}

bool RtlSdrBackend::available() const {
    return loader_.is_loaded();
}

std::vector<DeviceInfo> RtlSdrBackend::discover() {
    std::vector<DeviceInfo> devices;
    if (!available()) return devices;

    const auto& api = loader_.api();
    int count = 0;
    try {
        count = api.get_device_count();
    } catch (...) {
        return devices;
    }

    for (int i = 0; i < count; ++i) {
        char manufact[256] = {0};
        char product[256] = {0};
        char serial[256] = {0};

        if (api.get_device_usb_strings(i, manufact, product, serial) != 0) {
            // fallback
        }

        DeviceInfo info;
        info.backend_name = name();
        info.identifier = "rtl_sdr:" + std::to_string(i);
        info.display_name = std::string("RTL-SDR (") + std::to_string(i) + ")";
        
        if (manufact[0] != '\0') info.manufacturer = manufact;
        else info.manufacturer = "Realtek";
        
        if (product[0] != '\0') info.product = product;
        else info.product = "RTL-SDR";
        
        if (serial[0] != '\0') info.serial = serial;
        
        info.capabilities.has_rx = true;
        info.capabilities.has_tx = false;
        info.capabilities.has_gain = true;
        info.capabilities.supports_streaming = true;

        devices.push_back(info);
    }
    return devices;
}

std::shared_ptr<SDRDevice> RtlSdrBackend::open(const std::string& identifier) {
    if (!available()) {
        throw DeviceError("RTL-SDR backend is unavailable (library not loaded).");
    }

    auto devices = discover();
    for (const auto& d : devices) {
        if (d.identifier == identifier || (!d.serial.empty() && d.serial == identifier)) {
            // For now, extract index from identifier "rtl_sdr:X"
            size_t colon_pos = d.identifier.find(':');
            if (colon_pos == std::string::npos) throw DeviceError("Invalid identifier");
            int index = std::stoi(d.identifier.substr(colon_pos + 1));
            
            return std::make_shared<RtlSdrDevice>(loader_.api(), d);
        }
    }

    throw DeviceError("RTL-SDR device not found: " + identifier);
}

} // namespace backends
} // namespace sdrmon
