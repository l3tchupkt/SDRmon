#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace sdrmon {
namespace backends {

struct hackrf_transfer {
    void* device;
    uint8_t* buffer;
    int buffer_length;
    int valid_length;
    void* rx_ctx;
    void* tx_ctx;
};

struct hackrf_device_list_t {
    char** serial_numbers;
    void* usb_board_ids;
    int* usb_device_index;
    int devicecount;
    void** usb_devices;
    int usb_devicecount;
};

typedef int (*hackrf_sample_block_cb_fn)(hackrf_transfer* transfer);

struct HackRFApi {
    int (*hackrf_init)();
    int (*hackrf_exit)();
    hackrf_device_list_t* (*hackrf_device_list)();
    void (*hackrf_device_list_free)(hackrf_device_list_t* list);
    int (*hackrf_open)(void** device);
    int (*hackrf_open_by_serial)(const char* desired_serial_number, void** device);
    int (*hackrf_close)(void* device);
    int (*hackrf_start_rx)(void* device, hackrf_sample_block_cb_fn callback, void* rx_ctx);
    int (*hackrf_stop_rx)(void* device);
    int (*hackrf_set_freq)(void* device, uint64_t freq_hz);
    int (*hackrf_set_sample_rate)(void* device, double freq_hz);
    int (*hackrf_set_amp_enable)(void* device, uint8_t value);
    int (*hackrf_set_lna_gain)(void* device, uint32_t value);
    int (*hackrf_set_vga_gain)(void* device, uint32_t value);
    int (*hackrf_set_baseband_filter_bandwidth)(void* device, uint32_t bandwidth_hz);
};

class HackRFLoader {
public:
    static HackRFLoader& get() {
        static HackRFLoader instance;
        return instance;
    }

    ~HackRFLoader();

    bool load();
    bool is_loaded() const { return loaded_; }
    
    const HackRFApi& api() const { return api_; }

private:
    HackRFLoader() = default;
    HackRFLoader(const HackRFLoader&) = delete;
    HackRFLoader& operator=(const HackRFLoader&) = delete;

    bool load_from(const std::string& path);

    bool loaded_ = false;
    void* handle_ = nullptr;
    HackRFApi api_{};
};

} // namespace backends
} // namespace sdrmon
