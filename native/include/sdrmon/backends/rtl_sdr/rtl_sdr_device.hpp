#pragma once

#include "sdrmon/core/device.hpp"
#include "sdrmon/core/iq_stream.hpp"
#include "sdrmon/core/iq_block.hpp"
#include "sdrmon/backends/rtl_sdr/rtl_sdr_loader.hpp"
#include <atomic>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <string>

namespace sdrmon {
namespace backends {

class RtlSdrDevice;

class RtlSdrStream : public IQStream {
public:
    explicit RtlSdrStream(RtlSdrDevice* device);
    ~RtlSdrStream() override;

    void start() override;
    void stop() override;
    bool running() const override;
    std::optional<IQBlock> next_block() override;
    std::optional<IQBlock> try_next_block() override;
    size_t available() const override;

private:
    void stream_thread_func();

    RtlSdrDevice* device_;
    std::atomic<bool> running_{false};
    std::thread stream_thread_;

    // Simple bounded ring buffer
    static constexpr size_t QUEUE_SIZE = 16;
    std::vector<IQBlock> queue_;
    size_t head_ = 0;
    size_t tail_ = 0;
    size_t count_ = 0;

    mutable std::mutex mutex_;
    std::condition_variable cv_not_empty_;

    uint64_t sequence_number_ = 0;
};

class RtlSdrDevice : public SDRDevice {
public:
    RtlSdrDevice(const RtlSdrApi& api, const DeviceInfo& info);
    ~RtlSdrDevice() override;

    DeviceInfo info() const override;
    Capabilities capabilities() const override;
    
    void configure(const StreamConfig& config) override;
    void start() override;
    void stop() override;
    void close() override;
    std::shared_ptr<IQStream> stream() override;

    // Direct access to API and dev for the stream
    const RtlSdrApi& api() const { return api_; }
    rtlsdr_dev_t* handle() const { return handle_; }
    const StreamConfig& current_config() const { return config_; }

private:
    RtlSdrApi api_;
    DeviceInfo info_;
    Capabilities caps_;
    StreamConfig config_;
    
    rtlsdr_dev_t* handle_ = nullptr;
    std::shared_ptr<RtlSdrStream> stream_;
};

} // namespace backends
} // namespace sdrmon
