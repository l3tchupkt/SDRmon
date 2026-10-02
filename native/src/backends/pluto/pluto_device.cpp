#include "sdrmon/backends/pluto/pluto_device.hpp"
#include "sdrmon/core/errors.hpp"
#include <chrono>

namespace sdrmon {
namespace backends {

PlutoDevice::PlutoDevice(const DeviceInfo& info, iio_context* ctx, iio_device* dev)
    : info_(info), context_(ctx), device_(dev), is_open_(false), phy_(nullptr) {
}

PlutoDevice::~PlutoDevice() {
    close();
}

DeviceInfo PlutoDevice::info() const {
    return info_;
}

Capabilities PlutoDevice::capabilities() const {
    Capabilities caps;
    caps.has_rx = true;
    caps.has_tx = false;
    caps.has_gain = true;
    caps.has_bandwidth = true;
    caps.supported_sample_rates = {{2000000, 20000000}};
    for (int i = 0; i <= 73; i += 1) {
        caps.supported_gains.push_back(static_cast<double>(i));
    }
    return caps;
}

void PlutoDevice::open() {
    if (is_open_) return;
    auto& api = PlutoLoader::get().api();
    
    unsigned int dev_count = api.iio_context_get_devices_count(context_);
    for (unsigned int i = 0; i < dev_count; ++i) {
        iio_device* dev = api.iio_context_get_device(context_, i);
        std::string name = api.iio_device_get_name(dev) ? api.iio_device_get_name(dev) : "";
        std::string id = api.iio_device_get_id(dev) ? api.iio_device_get_id(dev) : "";
        
        if (name == "ad9361-phy" || id == "ad9361-phy") {
            phy_ = dev;
        } else if (name == "cf-ad9361-lpc") {
            device_ = dev;
        }
    }
    
    if (!phy_ || !device_) {
        throw DeviceOpenError("Failed to find necessary Pluto devices");
    }
    
    is_open_ = true;
}

void PlutoDevice::close() {
    if (is_open_) {
        stop();
        is_open_ = false;
    }
}

void PlutoDevice::configure(const StreamConfig& config) {
    if (!is_open_) throw ConfigurationError("Device not open");
    auto& api = PlutoLoader::get().api();
    
    iio_channel* altvoltage0 = api.iio_device_find_channel(phy_, "altvoltage0", true);
    if (!altvoltage0 || api.iio_channel_attr_write_longlong(altvoltage0, "frequency", config.center_frequency) < 0) {
        throw ConfigurationError("Failed to set Pluto frequency");
    }
    
    iio_channel* voltage0 = api.iio_device_find_channel(phy_, "voltage0", false);
    if (!voltage0 || api.iio_channel_attr_write_longlong(voltage0, "sampling_frequency", config.sample_rate) < 0) {
        throw ConfigurationError("Failed to set Pluto sample rate");
    }
    
    uint32_t bw = static_cast<uint32_t>(config.sample_rate * 0.8);
    api.iio_channel_attr_write_longlong(voltage0, "rf_bandwidth", bw);
    
    if (config.gain_value.has_value() && api.iio_channel_attr_write_double(voltage0, "hardwaregain", config.gain_value.value()) < 0) {
        throw ConfigurationError("Failed to set Pluto hardware gain");
    }
    
    config_ = config;
}

void PlutoDevice::start() {
    if (!stream_) {
        stream_ = std::make_shared<PlutoStream>(this);
    }
    stream_->start();
}

void PlutoDevice::stop() {
    if (stream_) {
        stream_->stop();
    }
}

std::shared_ptr<IQStream> PlutoDevice::stream() {
    if (!stream_) {
        stream_ = std::make_shared<PlutoStream>(this);
    }
    return stream_;
}

// --- PlutoStream ---

PlutoStream::PlutoStream(PlutoDevice* device)
    : device_(device) {
    queue_.resize(QUEUE_SIZE);
}

PlutoStream::~PlutoStream() {
    stop();
}

void PlutoStream::start() {
    if (running_) return;
    
    auto& api = PlutoLoader::get().api();
    
    rx0_i_ = api.iio_device_find_channel(device_->handle(), "voltage0", false);
    rx0_q_ = api.iio_device_find_channel(device_->handle(), "voltage1", false);
    
    if (!rx0_i_ || !rx0_q_) {
        throw StreamError("Failed to find rx0 I and Q channels");
    }
    
    api.iio_channel_enable(rx0_i_);
    api.iio_channel_enable(rx0_q_);
    
    buffer_ = api.iio_device_create_buffer(device_->handle(), 8192, false);
    if (!buffer_) {
        api.iio_channel_disable(rx0_i_);
        api.iio_channel_disable(rx0_q_);
        throw StreamError("Failed to create Pluto buffer");
    }
    
    {
        std::lock_guard<std::mutex> lock(mutex_);
        head_ = 0;
        tail_ = 0;
        count_ = 0;
        sequence_number_ = 0;
        running_ = true;
    }
    
    thread_ = std::thread(&PlutoStream::rx_thread, this);
}

void PlutoStream::rx_thread() {
    auto& api = PlutoLoader::get().api();
    
    while (running_) {
        ptrdiff_t ret = api.iio_buffer_refill(buffer_);
        if (ret < 0) {
            running_ = false;
            cv_not_empty_.notify_all();
            break;
        }
        
        ptrdiff_t inc = api.iio_buffer_step(buffer_);
        void* p_end = api.iio_buffer_end(buffer_);
        
        if (inc == 0) continue;
        
        size_t samples_count = (reinterpret_cast<uintptr_t>(p_end) - reinterpret_cast<uintptr_t>(api.iio_buffer_first(buffer_, rx0_i_))) / inc;
        
        IQBlock block;
        block.data.reserve(samples_count);
        
        for (void* ptr = api.iio_buffer_first(buffer_, rx0_i_); ptr < p_end; ptr = reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(ptr) + inc)) {
            int16_t* i_ptr = reinterpret_cast<int16_t*>(ptr);
            int16_t* q_ptr = reinterpret_cast<int16_t*>(reinterpret_cast<uintptr_t>(ptr) + 2); // Q is immediately after I usually
            
            float i_val = static_cast<float>(*i_ptr) / 2048.0f;
            float q_val = static_cast<float>(*q_ptr) / 2048.0f;
            block.data.emplace_back(i_val, q_val);
        }
        
        auto cfg = device_->current_config();
        block.sample_rate = cfg.sample_rate;
        block.center_frequency = cfg.center_frequency;
        
        auto now = std::chrono::system_clock::now().time_since_epoch();
        block.timestamp = std::chrono::duration_cast<std::chrono::duration<double>>(now).count();
        
        std::lock_guard<std::mutex> lock(mutex_);
        if (!running_) break;
        
        block.sequence_number = sequence_number_++;
        
        if (count_ < QUEUE_SIZE) {
            queue_[tail_] = std::move(block);
            tail_ = (tail_ + 1) % QUEUE_SIZE;
            count_++;
            cv_not_empty_.notify_one();
        }
    }
}

void PlutoStream::stop() {
    if (running_) {
        running_ = false;
        // Unblocking iio_buffer_refill can be tricky, typically it will timeout or cancel when disabled
    }
    
    if (thread_.joinable()) thread_.join();
    
    if (buffer_) {
        auto& api = PlutoLoader::get().api();
        api.iio_buffer_destroy(buffer_);
        buffer_ = nullptr;
        
        if (rx0_i_) api.iio_channel_disable(rx0_i_);
        if (rx0_q_) api.iio_channel_disable(rx0_q_);
    }
    
    std::lock_guard<std::mutex> lock(mutex_);
    cv_not_empty_.notify_all();
}

bool PlutoStream::running() const {
    return running_;
}

std::optional<IQBlock> PlutoStream::next_block() {
    std::unique_lock<std::mutex> lock(mutex_);
    cv_not_empty_.wait(lock, [this]() { return count_ > 0 || !running_; });
    
    if (count_ == 0 && !running_) return std::nullopt;
    
    auto block = std::move(queue_[head_]);
    head_ = (head_ + 1) % QUEUE_SIZE;
    count_--;
    return block;
}

std::optional<IQBlock> PlutoStream::try_next_block() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (count_ == 0) return std::nullopt;
    
    auto block = std::move(queue_[head_]);
    head_ = (head_ + 1) % QUEUE_SIZE;
    count_--;
    return block;
}

size_t PlutoStream::available() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return count_;
}

} // namespace backends
} // namespace sdrmon
