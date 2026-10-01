#pragma once

#include <vector>
#include <mutex>
#include <condition_variable>
#include <optional>
#include "iq_block.hpp"

namespace sdrmon {

class RingBuffer {
public:
    explicit RingBuffer(size_t max_size = 100) : max_size_(max_size) {}

    void push(IQBlock block) {
        std::unique_lock<std::mutex> lock(mutex_);
        if (queue_.size() >= max_size_) {
            // Drop oldest policy for live SDR monitoring
            queue_.erase(queue_.begin());
            dropped_blocks_++;
        }
        queue_.push_back(std::move(block));
        cv_.notify_one();
    }

    std::optional<IQBlock> pop(bool block = true) {
        std::unique_lock<std::mutex> lock(mutex_);
        if (block) {
            cv_.wait(lock, [this]() { return !queue_.empty() || closed_; });
        }
        
        if (queue_.empty()) {
            return std::nullopt;
        }

        auto item = std::move(queue_.front());
        queue_.erase(queue_.begin());
        return item;
    }

    void close() {
        std::unique_lock<std::mutex> lock(mutex_);
        closed_ = true;
        cv_.notify_all();
    }
    
    void clear() {
        std::unique_lock<std::mutex> lock(mutex_);
        queue_.clear();
    }
    
    size_t size() const {
        std::unique_lock<std::mutex> lock(mutex_);
        return queue_.size();
    }
    
    uint64_t dropped_count() const {
        return dropped_blocks_;
    }

private:
    size_t max_size_;
    std::vector<IQBlock> queue_;
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    bool closed_{false};
    uint64_t dropped_blocks_{0};
};

} // namespace sdrmon
