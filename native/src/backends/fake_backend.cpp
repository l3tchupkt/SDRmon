#include "sdrmon/backends/fake_backend.hpp"
#include "sdrmon/core/errors.hpp"
#include <chrono>
#include <cmath>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace sdrmon {

FakeStream::FakeStream(const StreamConfig& config)
    : config_(config), buffer_(std::make_shared<RingBuffer>(100)) {}

FakeStream::~FakeStream() {
    stop();
}

void FakeStream::start() {
    if (running_.exchange(true)) {
        return;
    }
    buffer_->clear();
    sequence_number_ = 0;
    phase_ = 0.0;
    thread_ = std::thread(&FakeStream::stream_thread_func, this);
}

void FakeStream::stop() {
    if (running_.exchange(false)) {
        buffer_->close();
        if (thread_.joinable()) {
            thread_.join();
        }
    }
}

bool FakeStream::running() const {
    return running_.load();
}

std::optional<IQBlock> FakeStream::next_block() {
    return buffer_->pop(true);
}

std::optional<IQBlock> FakeStream::try_next_block() {
    return buffer_->pop(false);
}

size_t FakeStream::available() const {
    return buffer_->size();
}

void FakeStream::stream_thread_func() {
    // Generate blocks at appropriate rate
    const double block_duration = config_.block_size / config_.sample_rate;
    auto next_time = std::chrono::steady_clock::now();
    
    // Create a deterministic signal
    double tone_freq = 50e3; // 50kHz offset tone
    double phase_inc = 2.0 * M_PI * tone_freq / config_.sample_rate;
    
    while (running_.load()) {
        next_time += std::chrono::nanoseconds(static_cast<long long>(block_duration * 1e9));
        
        // Wait until it's time for the next block
        std::this_thread::sleep_until(next_time);
        
        if (!running_.load()) {
            break;
        }
        
        IQBlock block;
        block.data.resize(config_.block_size);
        block.sequence_number = sequence_number_++;
        block.sample_count = config_.block_size;
        block.sample_rate = config_.sample_rate;
        block.center_frequency = config_.center_frequency;
        
        auto now = std::chrono::system_clock::now();
        block.timestamp = std::chrono::duration<double>(now.time_since_epoch()).count();
        
        // Generate complex exponential tone + noise
        for (size_t i = 0; i < config_.block_size; ++i) {
            float i_val = 0.5f * std::cos(phase_);
            float q_val = 0.5f * std::sin(phase_);
            
            // Add some basic noise
            float noise_i = ((rand() % 1000) / 1000.0f - 0.5f) * 0.1f;
            float noise_q = ((rand() % 1000) / 1000.0f - 0.5f) * 0.1f;
            
            block.data[i] = std::complex<float>(i_val + noise_i, q_val + noise_q);
            phase_ += phase_inc;
        }
        
        if (phase_ > 2.0 * M_PI) {
            phase_ -= 2.0 * M_PI;
        }
        
        buffer_->push(std::move(block));
    }
}

FakeDevice::FakeDevice(const std::string& identifier) 
    : identifier_(identifier) {}

FakeDevice::~FakeDevice() {
    close();
}

DeviceInfo FakeDevice::info() const {
    DeviceInfo i;
    i.backend_name = "FakeSDR";
    i.identifier = identifier_;
    i.serial = "FAKE-0001";
    i.display_name = "FakeSDR Device";
    i.manufacturer = "SDRmon";
    i.product = "Synthetic";
    i.capabilities = capabilities();
    return i;
}

Capabilities FakeDevice::capabilities() const {
    Capabilities cap;
    cap.has_rx = true;
    cap.has_tx = false;
    cap.supported_sample_rates = {{1.0e6, 20.0e6}};
    cap.supported_frequencies = {{10e6, 6000e6}};
    cap.has_gain = true;
    cap.supported_gains = {0.0, 10.0, 20.0, 30.0};
    cap.has_bandwidth = false;
    return cap;
}

void FakeDevice::configure(const StreamConfig& config) {
    if (stream_ && stream_->running()) {
        throw DeviceError("Cannot configure while streaming");
    }
    config_ = config;
}

void FakeDevice::start() {
    if (!stream_) {
        stream_ = std::make_shared<FakeStream>(config_);
    }
    stream_->start();
}

void FakeDevice::stop() {
    if (stream_) {
        stream_->stop();
    }
}

void FakeDevice::close() {
    stop();
    stream_.reset();
}

std::shared_ptr<IQStream> FakeDevice::stream() {
    if (!stream_) {
        throw StreamError("Stream not started");
    }
    return stream_;
}

std::vector<DeviceInfo> FakeBackend::discover() {
    std::vector<DeviceInfo> devices;
    FakeDevice dev("fake:0");
    devices.push_back(dev.info());
    return devices;
}

std::shared_ptr<SDRDevice> FakeBackend::open(const std::string& identifier) {
    if (identifier == "fake:0" || identifier == "fake") {
        return std::make_shared<FakeDevice>(identifier);
    }
    throw DeviceNotFoundError("Fake device not found: " + identifier);
}

} // namespace sdrmon
