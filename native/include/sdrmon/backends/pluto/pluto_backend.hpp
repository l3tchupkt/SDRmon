#pragma once

#include "sdrmon/core/backend.hpp"
#include <memory>

namespace sdrmon {
namespace backends {

struct iio_context;

class PlutoBackend : public SDRBackend {
public:
    PlutoBackend();
    ~PlutoBackend() override;

    std::string name() const override;
    bool available() const override;
    
    std::vector<DeviceInfo> discover() override;
    std::shared_ptr<SDRDevice> open(const std::string& identifier) override;

private:
    bool initialized_ = false;
    iio_context* default_context_ = nullptr;
};

} // namespace backends
} // namespace sdrmon
