#pragma once

#include <memory>
#include <atomic>
#include <thread>
#include "iq_block.hpp"
#include "ring_buffer.hpp"

namespace sdrmon {

class IQStream {
public:
    virtual ~IQStream() = default;

    virtual void start() = 0;
    virtual void stop() = 0;
    virtual bool running() const = 0;
    
    // Blocking wait for the next block
    virtual std::optional<IQBlock> next_block() = 0;
    
    // Non-blocking wait for the next block
    virtual std::optional<IQBlock> try_next_block() = 0;
    
    virtual size_t available() const = 0;
};

} // namespace sdrmon
