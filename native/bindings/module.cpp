#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <pybind11/numpy.h>

#include "sdrmon/core/manager.hpp"
#include "sdrmon/core/device.hpp"
#include "sdrmon/core/iq_stream.hpp"
#include "sdrmon/core/stream_config.hpp"
#include "sdrmon/core/device_info.hpp"
#include "sdrmon/core/capabilities.hpp"
#include "sdrmon/core/errors.hpp"

namespace py = pybind11;
using namespace sdrmon;

PYBIND11_MODULE(sdrmon_native, m) {
    m.doc() = "sdrmon native C++ core";

    // Exceptions
    static py::exception<SDRmonError> exc_sdrmon_error(m, "SDRmonError");
    static py::exception<DeviceError> exc_device_error(m, "DeviceError", exc_sdrmon_error.ptr());
    static py::exception<DeviceNotFoundError> exc_not_found(m, "DeviceNotFoundError", exc_device_error.ptr());
    static py::exception<StreamError> exc_stream_error(m, "StreamError", exc_sdrmon_error.ptr());

    py::register_exception_translator([](std::exception_ptr p) {
        try {
            if (p) std::rethrow_exception(p);
        } catch (const DeviceNotFoundError &e) {
            exc_not_found(e.what());
        } catch (const DeviceError &e) {
            exc_device_error(e.what());
        } catch (const StreamError &e) {
            exc_stream_error(e.what());
        } catch (const SDRmonError &e) {
            exc_sdrmon_error(e.what());
        }
    });

    // Capabilities
    py::class_<Capabilities>(m, "Capabilities")
        .def(py::init<>())
        .def_readwrite("has_rx", &Capabilities::has_rx)
        .def_readwrite("has_tx", &Capabilities::has_tx)
        .def_readwrite("supported_sample_rates", &Capabilities::supported_sample_rates)
        .def_readwrite("supported_frequencies", &Capabilities::supported_frequencies)
        .def_readwrite("has_gain", &Capabilities::has_gain)
        .def_readwrite("supported_gains", &Capabilities::supported_gains)
        .def_readwrite("has_bandwidth", &Capabilities::has_bandwidth)
        .def_readwrite("supported_bandwidths", &Capabilities::supported_bandwidths)
        .def_readwrite("has_frequency_correction", &Capabilities::has_frequency_correction)
        .def_readwrite("has_hardware_agc", &Capabilities::has_hardware_agc)
        .def_readwrite("supports_streaming", &Capabilities::supports_streaming);

    // DeviceInfo
    py::class_<DeviceInfo>(m, "DeviceInfo")
        .def(py::init<>())
        .def_readwrite("backend_name", &DeviceInfo::backend_name)
        .def_readwrite("identifier", &DeviceInfo::identifier)
        .def_readwrite("serial", &DeviceInfo::serial)
        .def_readwrite("display_name", &DeviceInfo::display_name)
        .def_readwrite("manufacturer", &DeviceInfo::manufacturer)
        .def_readwrite("product", &DeviceInfo::product)
        .def_readwrite("capabilities", &DeviceInfo::capabilities);

    // StreamConfig
    py::enum_<StreamConfig::GainMode>(m, "GainMode")
        .value("Automatic", StreamConfig::GainMode::Automatic)
        .value("Manual", StreamConfig::GainMode::Manual)
        .export_values();

    py::class_<StreamConfig>(m, "StreamConfig")
        .def(py::init<>())
        .def_readwrite("center_frequency", &StreamConfig::center_frequency)
        .def_readwrite("sample_rate", &StreamConfig::sample_rate)
        .def_readwrite("bandwidth", &StreamConfig::bandwidth)
        .def_readwrite("gain_mode", &StreamConfig::gain_mode)
        .def_readwrite("gain_value", &StreamConfig::gain_value)
        .def_readwrite("block_size", &StreamConfig::block_size)
        .def_readwrite("frequency_correction_ppm", &StreamConfig::frequency_correction_ppm);

    // IQBlock
    py::class_<IQBlock>(m, "IQBlock")
        .def_readonly("sequence_number", &IQBlock::sequence_number)
        .def_readonly("sample_count", &IQBlock::sample_count)
        .def_readonly("sample_rate", &IQBlock::sample_rate)
        .def_readonly("center_frequency", &IQBlock::center_frequency)
        .def_readonly("timestamp", &IQBlock::timestamp)
        .def_property_readonly("data", [](IQBlock& self) -> py::array_t<std::complex<float>> {
            // Create a numpy array that OWNS a copy of the data, or copies it.
            // Returning by value like this creates a copy into a new numpy array.
            // We want to avoid memory leaks or dangling pointers.
            auto arr = py::array_t<std::complex<float>>(self.data.size());
            auto buf = arr.request();
            std::memcpy(buf.ptr, self.data.data(), self.data.size() * sizeof(std::complex<float>));
            return arr;
        });

    // IQStream
    py::class_<IQStream, std::shared_ptr<IQStream>>(m, "IQStream")
        .def("start", [](IQStream& self) {
            py::gil_scoped_release release;
            self.start();
        })
        .def("stop", [](IQStream& self) {
            py::gil_scoped_release release;
            self.stop();
        })
        .def("running", &IQStream::running)
        .def("next_block", [](IQStream& self) {
            std::optional<IQBlock> block;
            {
                py::gil_scoped_release release;
                block = self.next_block();
            }
            return block;
        })
        .def("try_next_block", [](IQStream& self) {
            std::optional<IQBlock> block;
            {
                py::gil_scoped_release release;
                block = self.try_next_block();
            }
            return block;
        })
        .def("available", &IQStream::available);

    // SDRDevice
    py::class_<SDRDevice, std::shared_ptr<SDRDevice>>(m, "SDRDevice")
        .def("info", &SDRDevice::info)
        .def("capabilities", &SDRDevice::capabilities)
        .def("configure", [](SDRDevice& self, const StreamConfig& config) {
            py::gil_scoped_release release;
            self.configure(config);
        })
        .def("start", [](SDRDevice& self) {
            py::gil_scoped_release release;
            self.start();
        })
        .def("stop", [](SDRDevice& self) {
            py::gil_scoped_release release;
            self.stop();
        })
        .def("close", [](SDRDevice& self) {
            py::gil_scoped_release release;
            self.close();
        })
        .def("stream", &SDRDevice::stream);

    // SDRManager
    py::class_<SDRManager>(m, "SDRManager")
        .def(py::init<>())
        .def("backends", &SDRManager::backends)
        .def("discover", [](SDRManager& self) {
            py::gil_scoped_release release;
            return self.discover();
        })
        .def("open", [](SDRManager& self, const std::string& identifier) {
            py::gil_scoped_release release;
            return self.open(identifier);
        });
}
