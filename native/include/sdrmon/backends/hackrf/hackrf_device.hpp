#pragma once

#include "sdrmon/core/device.hpp"
#include "sdrmon/core/iq_stream.hpp"
#include "sdrmon/backends/hackrf/hackrf_loader.hpp"
#include <atomic>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>

namespace sdrmon {
namespace backends {

class HackRFDevice;

class HackRFStream : public IQStream {
public:
    HackRFStream(HackRFDevice* device);
    ~HackRFStream() override;

    void start() override;
    void stop() override;
    bool running() const override;
    std::optional<IQBlock> next_block() override;
    std::optional<IQBlock> try_next_block() override;
    size_t available() const override;

    static int rx_callback(hackrf_transfer* transfer);

private:
    HackRFDevice* device_;
    std::atomic<bool> running_{false};

    static constexpr size_t QUEUE_SIZE = 16;
    std::vector<IQBlock> queue_;
    size_t head_ = 0;
    size_t tail_ = 0;
    size_t count_ = 0;

    mutable std::mutex mutex_;
    std::condition_variable cv_not_empty_;
    uint64_t sequence_number_ = 0;
};

class HackRFDevice : public SDRDevice {
public:
    HackRFDevice(const DeviceInfo& info, void* device_handle);
    ~HackRFDevice() override;

    DeviceInfo info() const override;
    Capabilities capabilities() const override;

    void configure(const StreamConfig& config) override;
    void start() override;
    void stop() override;
    void close() override;

    std::shared_ptr<IQStream> stream() override;

    void* handle() const { return device_; }
    const StreamConfig& current_config() const { return config_; }

    void open(); // internal

private:
    DeviceInfo info_;
    void* device_;
    bool is_open_;
    StreamConfig config_;
    std::shared_ptr<HackRFStream> stream_;
};

} // namespace backends
} // namespace sdrmon
