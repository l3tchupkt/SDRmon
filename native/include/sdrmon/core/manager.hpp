#pragma once

#include <vector>
#include <string>
#include <memory>
#include <map>
#include "backend.hpp"
#include "device.hpp"

namespace sdrmon {

class SDRManager {
public:
    SDRManager();
    ~SDRManager();

    void register_backend(std::shared_ptr<SDRBackend> backend);
    std::vector<std::string> backends() const;
    
    std::vector<DeviceInfo> discover();
    std::shared_ptr<SDRDevice> open(const std::string& identifier);

private:
    std::map<std::string, std::shared_ptr<SDRBackend>> backends_;
};

} // namespace sdrmon
