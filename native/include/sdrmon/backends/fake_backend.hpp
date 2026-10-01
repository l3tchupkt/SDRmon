#pragma once

#include "sdrmon/core/backend.hpp"
#include "sdrmon/core/device.hpp"
#include "sdrmon/core/iq_stream.hpp"
#include "sdrmon/core/ring_buffer.hpp"

#include <thread>
#include <atomic>
#include <mutex>
#include <random>

namespace sdrmon {

class FakeStream : public IQStream {
public:
    explicit FakeStream(const StreamConfig& config);
    ~FakeStream() override;

    void start() override;
    void stop() override;
    bool running() const override;
    
    std::optional<IQBlock> next_block() override;
    std::optional<IQBlock> try_next_block() override;
    size_t available() const override;

private:
    void stream_thread_func();

    StreamConfig config_;
    std::shared_ptr<RingBuffer> buffer_;
    
    std::atomic<bool> running_{false};
    std::thread thread_;
    uint64_t sequence_number_{0};
    
    // Synthetic tone generation
    double phase_{0.0};
};

class FakeDevice : public SDRDevice {
public:
    explicit FakeDevice(const std::string& identifier);
    ~FakeDevice() override;

    DeviceInfo info() const override;
    Capabilities capabilities() const override;
    
    void configure(const StreamConfig& config) override;
    
    void start() override;
    void stop() override;
    void close() override;
    
    std::shared_ptr<IQStream> stream() override;

private:
    std::string identifier_;
    StreamConfig config_;
    std::shared_ptr<FakeStream> stream_;
};

class FakeBackend : public SDRBackend {
public:
    std::string name() const override { return "FakeSDR"; }
    bool available() const override { return true; }
    
    std::vector<DeviceInfo> discover() override;
    std::shared_ptr<SDRDevice> open(const std::string& identifier) override;
};

} // namespace sdrmon
