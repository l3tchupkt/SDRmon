#include "sdrmon/backends/pluto/pluto_backend.hpp"
#include "sdrmon/backends/pluto/pluto_loader.hpp"
#include "sdrmon/backends/pluto/pluto_device.hpp"
#include "sdrmon/core/errors.hpp"
#include <iostream>

namespace sdrmon {
namespace backends {

PlutoBackend::PlutoBackend() {
    if (PlutoLoader::get().load()) {
        auto& api = PlutoLoader::get().api();
        default_context_ = api.iio_create_default_context();
        if (default_context_) {
            initialized_ = true;
        }
    }
}

PlutoBackend::~PlutoBackend() {
    if (initialized_ && default_context_) {
        auto& api = PlutoLoader::get().api();
        api.iio_context_destroy(default_context_);
        initialized_ = false;
        default_context_ = nullptr;
    }
}

std::string PlutoBackend::name() const {
    return "pluto";
}

bool PlutoBackend::available() const {
    return initialized_;
}

std::vector<DeviceInfo> PlutoBackend::discover() {
    std::vector<DeviceInfo> devices;
    if (!initialized_) return devices;
    
    auto& api = PlutoLoader::get().api();
    unsigned int dev_count = api.iio_context_get_devices_count(default_context_);
    
    // Pluto usually has multiple devices in the context (ad9361-phy, cf-ad9361-lpc).
    // We just report one device for the context if ad9361-phy is found.
    bool has_pluto = false;
    for (unsigned int i = 0; i < dev_count; ++i) {
        iio_device* dev = api.iio_context_get_device(default_context_, i);
        if (api.iio_device_get_name(dev)) {
            std::string name = api.iio_device_get_name(dev);
            if (name == "ad9361-phy") {
                has_pluto = true;
                break;
            }
        }
    }
    
    if (has_pluto) {
        DeviceInfo info;
        info.backend_name = "pluto";
        info.manufacturer = "Analog Devices";
        info.product = "PlutoSDR";
        info.serial = "local";
        info.identifier = "pluto:local";
        devices.push_back(info);
    }
    
    // Optionally we could discover network devices via scan, but this is enough for now
    return devices;
}

std::shared_ptr<SDRDevice> PlutoBackend::open(const std::string& identifier) {
    if (!initialized_) throw BackendError("PlutoSDR backend not available");
    
    if (identifier.find("pluto:") != 0) {
        throw DeviceNotFoundError("Not a pluto identifier");
    }
    
    auto devices = discover();
    if (devices.empty()) {
        throw DeviceNotFoundError("PlutoSDR device not found");
    }
    
    // We just pass the default context and let PlutoDevice figure it out
    auto device = std::make_shared<PlutoDevice>(devices[0], default_context_, nullptr);
    device->open();
    return device;
}

} // namespace backends
} // namespace sdrmon
