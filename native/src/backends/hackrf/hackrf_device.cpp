#include "sdrmon/backends/hackrf/hackrf_device.hpp"
#include "sdrmon/core/errors.hpp"
#include <chrono>

namespace sdrmon {
namespace backends {

HackRFDevice::HackRFDevice(const DeviceInfo& info, void* device_handle)
    : info_(info), device_(device_handle), is_open_(false) {
}

HackRFDevice::~HackRFDevice() {
    close();
}

DeviceInfo HackRFDevice::info() const {
    return info_;
}

Capabilities HackRFDevice::capabilities() const {
    Capabilities caps;
    caps.has_rx = true;
    caps.has_tx = false;
    caps.has_gain = true;
    caps.has_bandwidth = true;
    caps.supported_sample_rates = {{2000000, 20000000}};
    
    for (int i = 0; i <= 102; i += 2) {
        caps.supported_gains.push_back(static_cast<double>(i));
    }
    return caps;
}

void HackRFDevice::open() {
    if (is_open_) return;
    
    auto& api = HackRFLoader::get().api();
    if (!device_) {
        if (info_.serial.empty()) {
            if (api.hackrf_open(&device_) != 0) throw DeviceOpenError("Failed to open HackRF");
        } else {
            if (api.hackrf_open_by_serial(info_.serial.c_str(), &device_) != 0) throw DeviceOpenError("Failed to open HackRF by serial");
        }
    }
    
    is_open_ = true;
    api.hackrf_set_amp_enable(device_, 0);
}

void HackRFDevice::close() {
    if (is_open_ && device_) {
        stop();
        auto& api = HackRFLoader::get().api();
        api.hackrf_close(device_);
        device_ = nullptr;
        is_open_ = false;
    }
}

void HackRFDevice::configure(const StreamConfig& config) {
    if (!is_open_) throw ConfigurationError("Device not open");
    
    config_ = config;
    
    auto& api = HackRFLoader::get().api();
    if (api.hackrf_set_freq(device_, static_cast<uint64_t>(config.center_frequency)) != 0) {
        throw ConfigurationError("Failed to set HackRF frequency");
    }
    if (api.hackrf_set_sample_rate(device_, config.sample_rate) != 0) {
        throw ConfigurationError("Failed to set HackRF sample rate");
    }
    
    uint32_t bw = static_cast<uint32_t>(config.sample_rate * 0.75);
    api.hackrf_set_baseband_filter_bandwidth(device_, bw);
    
    int target = std::max(0, std::min(102, static_cast<int>(config.gain_value.value_or(0.0))));
    int lna = std::min(40, (target / 8) * 8);
    int vga = std::min(62, ((target - lna) / 2) * 2);
    
    api.hackrf_set_lna_gain(device_, static_cast<uint32_t>(lna));
    api.hackrf_set_vga_gain(device_, static_cast<uint32_t>(vga));
}

void HackRFDevice::start() {
    if (!stream_) {
        stream_ = std::make_shared<HackRFStream>(this);
    }
    stream_->start();
}

void HackRFDevice::stop() {
    if (stream_) {
        stream_->stop();
    }
}

std::shared_ptr<IQStream> HackRFDevice::stream() {
    if (!stream_) {
        stream_ = std::make_shared<HackRFStream>(this);
    }
    return stream_;
}


// --- HackRFStream ---

HackRFStream::HackRFStream(HackRFDevice* device)
    : device_(device) {
    queue_.resize(QUEUE_SIZE);
}

HackRFStream::~HackRFStream() {
    stop();
}

int HackRFStream::rx_callback(hackrf_transfer* transfer) {
    if (!transfer->rx_ctx) return 0;
    
    auto stream = static_cast<HackRFStream*>(transfer->rx_ctx);
    if (!stream->running_ || transfer->valid_length <= 0) {
        return 0;
    }
    
    int num_samples = transfer->valid_length / 2;
    IQBlock block;
    block.data.resize(num_samples);
    
    const int8_t* raw = reinterpret_cast<const int8_t*>(transfer->buffer);
    for (int i = 0; i < num_samples; ++i) {
        float i_val = static_cast<float>(raw[2 * i]) / 128.0f;
        float q_val = static_cast<float>(raw[2 * i + 1]) / 128.0f;
        block.data[i] = std::complex<float>(i_val, q_val);
    }
    
    auto cfg = stream->device_->current_config();
    block.sample_rate = cfg.sample_rate;
    block.center_frequency = cfg.center_frequency;
    block.sample_count = num_samples;
    
    auto now = std::chrono::system_clock::now().time_since_epoch();
    block.timestamp = std::chrono::duration_cast<std::chrono::duration<double>>(now).count();
    
    std::lock_guard<std::mutex> lock(stream->mutex_);
    block.sequence_number = stream->sequence_number_++;
    
    if (stream->count_ < QUEUE_SIZE) {
        stream->queue_[stream->tail_] = std::move(block);
        stream->tail_ = (stream->tail_ + 1) % QUEUE_SIZE;
        stream->count_++;
        stream->cv_not_empty_.notify_one();
    } // else drop block
    
    return 0;
}

void HackRFStream::start() {
    if (running_) return;
    
    {
        std::lock_guard<std::mutex> lock(mutex_);
        head_ = 0;
        tail_ = 0;
        count_ = 0;
        sequence_number_ = 0;
        running_ = true;
    }
    
    auto& api = HackRFLoader::get().api();
    if (api.hackrf_start_rx(device_->handle(), rx_callback, this) != 0) {
        running_ = false;
        throw StreamError("Failed to start HackRF RX stream");
    }
}

void HackRFStream::stop() {
    if (running_) {
        auto& api = HackRFLoader::get().api();
        api.hackrf_stop_rx(device_->handle());
        
        std::lock_guard<std::mutex> lock(mutex_);
        running_ = false;
        cv_not_empty_.notify_all();
    }
}

bool HackRFStream::running() const {
    return running_;
}

std::optional<IQBlock> HackRFStream::next_block() {
    std::unique_lock<std::mutex> lock(mutex_);
    cv_not_empty_.wait(lock, [this]() { return count_ > 0 || !running_; });
    
    if (count_ == 0 && !running_) return std::nullopt;
    
    auto block = std::move(queue_[head_]);
    head_ = (head_ + 1) % QUEUE_SIZE;
    count_--;
    return block;
}

std::optional<IQBlock> HackRFStream::try_next_block() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (count_ == 0) return std::nullopt;
    
    auto block = std::move(queue_[head_]);
    head_ = (head_ + 1) % QUEUE_SIZE;
    count_--;
    return block;
}

size_t HackRFStream::available() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return count_;
}

} // namespace backends
} // namespace sdrmon
