#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace sdrmon {
namespace backends {

struct iio_context;
struct iio_device;
struct iio_channel;
struct iio_buffer;

struct PlutoApi {
    iio_context* (*iio_create_default_context)();
    iio_context* (*iio_create_network_context)(const char* host);
    void (*iio_context_destroy)(iio_context* ctx);
    
    unsigned int (*iio_context_get_devices_count)(const iio_context* ctx);
    iio_device* (*iio_context_get_device)(const iio_context* ctx, unsigned int index);
    
    const char* (*iio_device_get_name)(const iio_device* dev);
    const char* (*iio_device_get_id)(const iio_device* dev);
    
    iio_channel* (*iio_device_find_channel)(const iio_device* dev, const char* name, bool output);
    long long (*iio_channel_attr_write_longlong)(iio_channel* chn, const char* attr, long long val);
    long long (*iio_channel_attr_write_double)(iio_channel* chn, const char* attr, double val);
    void (*iio_channel_enable)(iio_channel* chn);
    void (*iio_channel_disable)(iio_channel* chn);
    
    iio_buffer* (*iio_device_create_buffer)(const iio_device* dev, size_t samples_count, bool cyclic);
    void (*iio_buffer_destroy)(iio_buffer* buf);
    
    ptrdiff_t (*iio_buffer_refill)(iio_buffer* buf);
    void* (*iio_buffer_first)(const iio_buffer* buf, const iio_channel* chn);
    void* (*iio_buffer_end)(const iio_buffer* buf);
    ptrdiff_t (*iio_buffer_step)(const iio_buffer* buf);
};

class PlutoLoader {
public:
    static PlutoLoader& get() {
        static PlutoLoader instance;
        return instance;
    }

    ~PlutoLoader();

    bool load();
    bool is_loaded() const { return loaded_; }
    
    const PlutoApi& api() const { return api_; }

private:
    PlutoLoader() = default;
    PlutoLoader(const PlutoLoader&) = delete;
    PlutoLoader& operator=(const PlutoLoader&) = delete;

    bool load_from(const std::string& path);

    bool loaded_ = false;
    void* handle_ = nullptr;
    PlutoApi api_{};
};

} // namespace backends
} // namespace sdrmon
