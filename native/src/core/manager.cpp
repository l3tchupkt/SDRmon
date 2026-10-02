#include "sdrmon/core/manager.hpp"
#include "sdrmon/backends/fake_backend.hpp"
#include "sdrmon/backends/rtl_sdr/rtl_sdr_backend.hpp"
#include "sdrmon/core/errors.hpp"

namespace sdrmon {

SDRManager::SDRManager() {
    register_backend(std::make_shared<FakeBackend>());
    register_backend(std::make_shared<backends::RtlSdrBackend>());
}

SDRManager::~SDRManager() = default;

void SDRManager::register_backend(std::shared_ptr<SDRBackend> backend) {
    if (backend) {
        backends_[backend->name()] = backend;
    }
}

std::vector<std::string> SDRManager::backends() const {
    std::vector<std::string> names;
    for (const auto& [name, backend] : backends_) {
        if (backend->available()) {
            names.push_back(name);
        }
    }
    return names;
}

std::vector<DeviceInfo> SDRManager::discover() {
    std::vector<DeviceInfo> all_devices;
    for (const auto& [_, backend] : backends_) {
        if (backend->available()) {
            auto devices = backend->discover();
            all_devices.insert(all_devices.end(), devices.begin(), devices.end());
        }
    }
    return all_devices;
}

std::shared_ptr<SDRDevice> SDRManager::open(const std::string& identifier) {
    for (const auto& [_, backend] : backends_) {
        if (backend->available()) {
            try {
                auto device = backend->open(identifier);
                if (device) {
                    return device;
                }
            } catch (const DeviceNotFoundError&) {
                // Continue searching other backends
            }
        }
    }
    throw DeviceNotFoundError("Device not found: " + identifier);
}

} // namespace sdrmon
