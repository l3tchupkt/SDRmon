#include "sdrmon/backends/rtl_sdr/rtl_sdr_device.hpp"
#include "sdrmon/core/errors.hpp"
#include <iostream>
#include <chrono>

namespace sdrmon {
namespace backends {

RtlSdrStream::RtlSdrStream(RtlSdrDevice* device) : device_(device) {}

RtlSdrStream::~RtlSdrStream() {
    stop();
}

void RtlSdrStream::start() {
    if (running_.load()) return;
    
    // Clear queue
    {
        std::lock_guard<std::mutex> lock(mutex_);
        queue_.clear();
        head_ = 0;
        tail_ = 0;
        count_ = 0;
        queue_.resize(QUEUE_SIZE);
        sequence_number_ = 0;
    }
    
    // Reset buffer on device
    auto handle = device_->handle();
    if (handle && device_->api().reset_buffer) {
        device_->api().reset_buffer(handle);
    }
    
    running_.store(true);
    stream_thread_ = std::thread(&RtlSdrStream::stream_thread_func, this);
}

void RtlSdrStream::stop() {
    if (!running_.load()) return;
    running_.store(false);
    if (stream_thread_.joinable()) {
        stream_thread_.join();
    }
}

bool RtlSdrStream::running() const {
    return running_.load();
}

std::optional<IQBlock> RtlSdrStream::next_block() {
    std::unique_lock<std::mutex> lock(mutex_);
    cv_not_empty_.wait(lock, [this]() {
        return count_ > 0 || !running_.load();
    });
    
    if (count_ == 0) return std::nullopt;
    
    auto block = std::move(queue_[tail_]);
    tail_ = (tail_ + 1) % QUEUE_SIZE;
    --count_;
    return block;
}

std::optional<IQBlock> RtlSdrStream::try_next_block() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (count_ == 0) return std::nullopt;
    
    auto block = std::move(queue_[tail_]);
    tail_ = (tail_ + 1) % QUEUE_SIZE;
    --count_;
    return block;
}

size_t RtlSdrStream::available() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return count_;
}

void RtlSdrStream::stream_thread_func() {
    auto handle = device_->handle();
    const auto& api = device_->api();
    const auto& config = device_->current_config();
    
    if (!handle || !api.read_sync) {
        running_.store(false);
        return;
    }
    
    // Native block size in bytes. RTL-SDR returns uint8 interleaved I/Q.
    // 2 bytes per sample.
    int block_samples = config.block_size > 0 ? static_cast<int>(config.block_size) : 65536;
    int bytes_to_read = block_samples * 2;
    std::vector<uint8_t> buffer(bytes_to_read);
    
    while (running_.load()) {
        int n_read = 0;
        int res = api.read_sync(handle, buffer.data(), bytes_to_read, &n_read);
        
        if (res < 0) {
            std::cerr << "RTL-SDR read_sync failed: " << res << std::endl;
            running_.store(false);
            break;
        }
        
        if (n_read > 0) {
            int samples_read = n_read / 2;
            IQBlock block;
            block.data.resize(samples_read);
            
            // Convert to complex float
            for (int i = 0; i < samples_read; ++i) {
                float i_val = (static_cast<float>(buffer[i * 2]) - 127.5f) / 127.5f;
                float q_val = (static_cast<float>(buffer[i * 2 + 1]) - 127.5f) / 127.5f;
                block.data[i] = std::complex<float>(i_val, q_val);
            }
            
            block.sequence_number = sequence_number_++;
            block.sample_count = samples_read;
            block.sample_rate = config.sample_rate;
            block.center_frequency = config.center_frequency;
            
            auto now = std::chrono::system_clock::now();
            block.timestamp = std::chrono::duration<double>(now.time_since_epoch()).count();
            
            // Push to queue
            {
                std::lock_guard<std::mutex> lock(mutex_);
                if (count_ == QUEUE_SIZE) {
                    // Drop oldest block to prevent unbound latency
                    tail_ = (tail_ + 1) % QUEUE_SIZE;
                    --count_;
                }
                queue_[head_] = std::move(block);
                head_ = (head_ + 1) % QUEUE_SIZE;
                ++count_;
            }
            cv_not_empty_.notify_one();
        }
    }
    cv_not_empty_.notify_all();
}

RtlSdrDevice::RtlSdrDevice(const RtlSdrApi& api, const DeviceInfo& info) 
    : api_(api), info_(info) {
    // Determine the index. info.identifier is "rtl_sdr:X"
    size_t pos = info_.identifier.find(':');
    int index = std::stoi(info_.identifier.substr(pos + 1));
    
    if (api_.open(&handle_, index) < 0 || !handle_) {
        throw DeviceError("Failed to open RTL-SDR device at index " + std::to_string(index));
    }
}

RtlSdrDevice::~RtlSdrDevice() {
    close();
}

DeviceInfo RtlSdrDevice::info() const {
    return info_;
}

Capabilities RtlSdrDevice::capabilities() const {
    return info_.capabilities;
}

void RtlSdrDevice::configure(const StreamConfig& config) {
    if (!handle_) throw DeviceError("Device not open");
    
    if (api_.set_center_freq(handle_, static_cast<uint32_t>(config.center_frequency)) < 0) {
        throw StreamError("Failed to set center frequency");
    }
    
    if (api_.set_sample_rate(handle_, static_cast<uint32_t>(config.sample_rate)) < 0) {
        throw StreamError("Failed to set sample rate");
    }
    
    if (api_.set_tuner_gain_mode) {
        api_.set_tuner_gain_mode(handle_, config.gain_mode == StreamConfig::GainMode::Manual ? 1 : 0);
        if (config.gain_mode == StreamConfig::GainMode::Manual && api_.set_tuner_gain && config.gain_value.has_value()) {
            // gain_value is likely float in API but librtlsdr uses integer tenths of dB.
            // E.g. 20.0 dB -> 200.
            int igain = static_cast<int>(config.gain_value.value() * 10.0f);
            api_.set_tuner_gain(handle_, igain);
        }
    }
    
    if (config.bandwidth.has_value() && config.bandwidth.value() > 0 && api_.set_tuner_bandwidth) {
        api_.set_tuner_bandwidth(handle_, static_cast<uint32_t>(config.bandwidth.value()));
    }
    
    config_ = config;
}

void RtlSdrDevice::start() {
    if (!handle_) throw DeviceError("Device not open");
    if (!stream_) {
        stream_ = std::make_shared<RtlSdrStream>(this);
    }
    stream_->start();
}

void RtlSdrDevice::stop() {
    if (stream_) {
        stream_->stop();
    }
}

void RtlSdrDevice::close() {
    stop();
    if (handle_) {
        api_.close(handle_);
        handle_ = nullptr;
    }
}

std::shared_ptr<IQStream> RtlSdrDevice::stream() {
    if (!stream_) {
        stream_ = std::make_shared<RtlSdrStream>(this);
    }
    return stream_;
}

} // namespace backends
} // namespace sdrmon
