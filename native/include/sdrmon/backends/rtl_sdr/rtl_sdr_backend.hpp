#pragma once

#include "sdrmon/core/manager.hpp"
#include "sdrmon/backends/rtl_sdr/rtl_sdr_loader.hpp"
#include <memory>

namespace sdrmon {
namespace backends {

class RtlSdrBackend : public SDRBackend {
public:
    RtlSdrBackend();
    ~RtlSdrBackend() override = default;

    std::string name() const override;
    bool available() const override;
    std::vector<DeviceInfo> discover() override;
    std::shared_ptr<SDRDevice> open(const std::string& identifier) override;

private:
    RtlSdrLoader& loader_;
};

} // namespace backends
} // namespace sdrmon
