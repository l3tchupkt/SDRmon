#include <catch2/catch_all.hpp>
#include "sdrmon/core/manager.hpp"

using namespace sdrmon;

TEST_CASE("SDRManager registers FakeBackend", "[manager]") {
    SDRManager manager;
    
    auto backends = manager.backends();
    REQUIRE(backends.size() >= 1);
    
    bool found_fake = false;
    for (const auto& b : backends) {
        if (b == "FakeSDR") found_fake = true;
    }
    REQUIRE(found_fake);
}

TEST_CASE("SDRManager discover FakeSDR", "[manager]") {
    SDRManager manager;
    auto devices = manager.discover();
    
    REQUIRE_FALSE(devices.empty());
    
    bool found = false;
    for (const auto& d : devices) {
        if (d.identifier == "fake:0") {
            found = true;
            REQUIRE(d.backend_name == "FakeSDR");
        }
    }
    REQUIRE(found);
}
