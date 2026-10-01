#define CATCH_CONFIG_MAIN
#include <catch2/catch_all.hpp>
#include "sdrmon/core/ring_buffer.hpp"
#include <thread>
#include <chrono>

using namespace sdrmon;

TEST_CASE("RingBuffer basic operations", "[ring_buffer]") {
    RingBuffer buffer(5);
    
    REQUIRE(buffer.size() == 0);
    
    IQBlock b1;
    b1.sequence_number = 1;
    buffer.push(b1);
    REQUIRE(buffer.size() == 1);
    
    auto out = buffer.pop(false);
    REQUIRE(out.has_value());
    REQUIRE(out->sequence_number == 1);
    REQUIRE(buffer.size() == 0);
}

TEST_CASE("RingBuffer overflow drops oldest", "[ring_buffer]") {
    RingBuffer buffer(3);
    
    for (int i = 0; i < 5; ++i) {
        IQBlock b;
        b.sequence_number = i;
        buffer.push(b);
    }
    
    REQUIRE(buffer.size() == 3);
    REQUIRE(buffer.dropped_count() == 2);
    
    auto out1 = buffer.pop(false);
    REQUIRE(out1.has_value());
    REQUIRE(out1->sequence_number == 2); // 0 and 1 were dropped
}

TEST_CASE("RingBuffer blocking pop", "[ring_buffer]") {
    RingBuffer buffer(5);
    
    std::thread t([&buffer]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        IQBlock b;
        b.sequence_number = 42;
        buffer.push(b);
    });
    
    auto out = buffer.pop(true);
    REQUIRE(out.has_value());
    REQUIRE(out->sequence_number == 42);
    
    t.join();
}

TEST_CASE("RingBuffer close unblocks", "[ring_buffer]") {
    RingBuffer buffer(5);
    
    std::thread t([&buffer]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        buffer.close();
    });
    
    auto out = buffer.pop(true);
    REQUIRE_FALSE(out.has_value());
    
    t.join();
}
