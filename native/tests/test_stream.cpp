#include <catch2/catch_all.hpp>
#include "sdrmon/core/manager.hpp"
#include <thread>
#include <chrono>

using namespace sdrmon;

TEST_CASE("FakeStream lifecycle and streaming", "[stream]") {
    SDRManager manager;
    auto dev = manager.open("fake:0");
    REQUIRE(dev != nullptr);
    
    StreamConfig config;
    config.sample_rate = 100e3;
    config.block_size = 1024;
    dev->configure(config);
    
    dev->start();
    
    auto stream = dev->stream();
    REQUIRE(stream != nullptr);
    REQUIRE(stream->running());
    
    // Read a few blocks
    for (int i = 0; i < 3; ++i) {
        auto block = stream->next_block();
        REQUIRE(block.has_value());
        REQUIRE(block->sample_count == 1024);
        REQUIRE(block->data.size() == 1024);
    }
    
    dev->stop();
    REQUIRE_FALSE(stream->running());
    
    // Queue should be empty or return immediately
    auto block = stream->next_block();
    REQUIRE_FALSE(block.has_value());
}
