#pragma once

#include <string>
#include <vector>
#include <memory>
#include <cstdint>

namespace sdrmon {
namespace backends {

struct rtlsdr_dev_t;

struct RtlSdrApi {
    int (*get_device_count)(void) = nullptr;
    const char* (*get_device_name)(uint32_t index) = nullptr;
    int (*get_device_usb_strings)(uint32_t index, char *manufact, char *product, char *serial) = nullptr;
    int (*open)(rtlsdr_dev_t **dev, uint32_t index) = nullptr;
    int (*close)(rtlsdr_dev_t *dev) = nullptr;
    int (*set_center_freq)(rtlsdr_dev_t *dev, uint32_t freq) = nullptr;
    uint32_t (*get_center_freq)(rtlsdr_dev_t *dev) = nullptr;
    int (*set_sample_rate)(rtlsdr_dev_t *dev, uint32_t rate) = nullptr;
    uint32_t (*get_sample_rate)(rtlsdr_dev_t *dev) = nullptr;
    int (*set_tuner_gain)(rtlsdr_dev_t *dev, int gain) = nullptr;
    int (*get_tuner_gains)(rtlsdr_dev_t *dev, int *gains) = nullptr;
    int (*set_tuner_gain_mode)(rtlsdr_dev_t *dev, int manual) = nullptr;
    int (*set_agc_mode)(rtlsdr_dev_t *dev, int on) = nullptr;
    int (*set_tuner_bandwidth)(rtlsdr_dev_t *dev, uint32_t bw) = nullptr;
    int (*reset_buffer)(rtlsdr_dev_t *dev) = nullptr;
    int (*read_sync)(rtlsdr_dev_t *dev, void *buf, int len, int *n_read) = nullptr;
};

class RtlSdrLoader {
public:
    static RtlSdrLoader& get() {
        static RtlSdrLoader instance;
        return instance;
    }

    bool load();
    bool is_loaded() const { return loaded_; }
    const RtlSdrApi& api() const { return api_; }
    
    // Attempt to open the library from a specific path (for testing or if in the same dir)
    bool load_from(const std::string& path);

private:
    RtlSdrLoader() = default;
    ~RtlSdrLoader();
    RtlSdrLoader(const RtlSdrLoader&) = delete;
    RtlSdrLoader& operator=(const RtlSdrLoader&) = delete;

    bool loaded_ = false;
    void* handle_ = nullptr;
    RtlSdrApi api_;
};

} // namespace backends
} // namespace sdrmon
