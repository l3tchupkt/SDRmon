#pragma once

#include <memory>
#include "device_info.hpp"
#include "stream_config.hpp"
#include "iq_stream.hpp"

namespace sdrmon {

class SDRDevice {
public:
    virtual ~SDRDevice() = default;

    virtual DeviceInfo info() const = 0;
    virtual Capabilities capabilities() const = 0;
    
    virtual void configure(const StreamConfig& config) = 0;
    
    virtual void start() = 0;
    virtual void stop() = 0;
    virtual void close() = 0;
    
    virtual std::shared_ptr<IQStream> stream() = 0;
};

} // namespace sdrmon
