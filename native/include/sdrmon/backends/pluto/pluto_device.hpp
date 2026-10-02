#pragma once

#include "sdrmon/core/device.hpp"
#include "sdrmon/core/iq_stream.hpp"
#include "sdrmon/backends/pluto/pluto_loader.hpp"
#include <atomic>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>

namespace sdrmon {
namespace backends {

class PlutoDevice;

class PlutoStream : public IQStream {
public:
    PlutoStream(PlutoDevice* device);
    ~PlutoStream() override;

    void start() override;
    void stop() override;
    bool running() const override;
    std::optional<IQBlock> next_block() override;
    std::optional<IQBlock> try_next_block() override;
    size_t available() const override;

private:
    void rx_thread();

    PlutoDevice* device_;
    std::atomic<bool> running_{false};
    iio_buffer* buffer_ = nullptr;
    iio_channel* rx0_i_ = nullptr;
    iio_channel* rx0_q_ = nullptr;

    std::thread thread_;

    static constexpr size_t QUEUE_SIZE = 16;
    std::vector<IQBlock> queue_;
    size_t head_ = 0;
    size_t tail_ = 0;
    size_t count_ = 0;

    mutable std::mutex mutex_;
    std::condition_variable cv_not_empty_;
    uint64_t sequence_number_ = 0;
};

class PlutoDevice : public SDRDevice {
public:
    PlutoDevice(const DeviceInfo& info, iio_context* ctx, iio_device* dev);
    ~PlutoDevice() override;

    DeviceInfo info() const override;
    Capabilities capabilities() const override;

    void configure(const StreamConfig& config) override;
    void start() override;
    void stop() override;
    void close() override;

    std::shared_ptr<IQStream> stream() override;

    iio_device* handle() const { return device_; }
    const StreamConfig& current_config() const { return config_; }

    void open();

private:
    DeviceInfo info_;
    iio_context* context_;
    iio_device* device_;
    bool is_open_;
    StreamConfig config_;
    
    iio_device* phy_;
    std::shared_ptr<PlutoStream> stream_;
};

} // namespace backends
} // namespace sdrmon
