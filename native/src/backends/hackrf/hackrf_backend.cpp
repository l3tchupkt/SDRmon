#include "sdrmon/backends/hackrf/hackrf_backend.hpp"
#include "sdrmon/backends/hackrf/hackrf_loader.hpp"
#include "sdrmon/backends/hackrf/hackrf_device.hpp"
#include "sdrmon/core/errors.hpp"

namespace sdrmon {
namespace backends {

HackRFBackend::HackRFBackend() {
    if (HackRFLoader::get().load()) {
        auto& api = HackRFLoader::get().api();
        if (api.hackrf_init() == 0) {
            initialized_ = true;
        }
    }
}

HackRFBackend::~HackRFBackend() {
    if (initialized_) {
        auto& api = HackRFLoader::get().api();
        api.hackrf_exit();
        initialized_ = false;
    }
}

std::string HackRFBackend::name() const {
    return "hackrf";
}

bool HackRFBackend::available() const {
    return initialized_;
}

std::vector<DeviceInfo> HackRFBackend::discover() {
    std::vector<DeviceInfo> devices;
    if (!initialized_) return devices;
    
    auto& api = HackRFLoader::get().api();
    auto list = api.hackrf_device_list();
    if (!list) return devices;
    
    for (int i = 0; i < list->devicecount; ++i) {
        DeviceInfo info;
        info.backend_name = "hackrf";
        info.manufacturer = "Great Scott Gadgets";
        info.product = "HackRF One";
        
        if (list->serial_numbers && list->serial_numbers[i]) {
            info.serial = list->serial_numbers[i];
        } else {
            info.serial = std::to_string(i); // Fallback
        }
        
        info.identifier = "hackrf:" + info.serial;
        devices.push_back(info);
    }
    
    api.hackrf_device_list_free(list);
    return devices;
}

std::shared_ptr<SDRDevice> HackRFBackend::open(const std::string& identifier) {
    if (!initialized_) throw BackendError("HackRF backend not available");
    
    // Identifier format: hackrf:<serial>
    if (identifier.find("hackrf:") != 0) {
        throw DeviceNotFoundError("Not a hackrf identifier");
    }
    
    std::string serial = identifier.substr(7);
    
    // Validate existence
    auto devices = discover();
    bool found = false;
    DeviceInfo target_info;
    
    for (const auto& dev : devices) {
        if (dev.serial == serial || dev.identifier == identifier) {
            found = true;
            target_info = dev;
            break;
        }
    }
    
    if (!found) {
        throw DeviceNotFoundError("HackRF device not found");
    }
    
    auto device = std::make_shared<HackRFDevice>(target_info, nullptr);
    device->open();
    return device;
}

} // namespace backends
} // namespace sdrmon
