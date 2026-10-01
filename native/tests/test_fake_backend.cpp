#include <catch2/catch_all.hpp>
#include "sdrmon/backends/fake_backend.hpp"

using namespace sdrmon;

TEST_CASE("FakeBackend open and capabilities", "[fake_backend]") {
    FakeBackend backend;
    
    REQUIRE(backend.name() == "FakeSDR");
    REQUIRE(backend.available());
    
    auto dev = backend.open("fake:0");
    REQUIRE(dev != nullptr);
    
    auto caps = dev->capabilities();
    REQUIRE(caps.has_rx == true);
    REQUIRE(caps.has_tx == false);
    
    auto info = dev->info();
    REQUIRE(info.identifier == "fake:0");
}
