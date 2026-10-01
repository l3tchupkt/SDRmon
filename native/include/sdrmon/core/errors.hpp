#pragma once

#include <stdexcept>
#include <string>

namespace sdrmon {

class SDRmonError : public std::runtime_error {
public:
    explicit SDRmonError(const std::string& message) : std::runtime_error(message) {}
};

class DeviceError : public SDRmonError {
public:
    explicit DeviceError(const std::string& message) : SDRmonError(message) {}
};

class DeviceNotFoundError : public DeviceError {
public:
    explicit DeviceNotFoundError(const std::string& message) : DeviceError(message) {}
};

class DeviceOpenError : public DeviceError {
public:
    explicit DeviceOpenError(const std::string& message) : DeviceError(message) {}
};

class DeviceDisconnectedError : public DeviceError {
public:
    explicit DeviceDisconnectedError(const std::string& message) : DeviceError(message) {}
};

class DevicePermissionError : public DeviceError {
public:
    explicit DevicePermissionError(const std::string& message) : DeviceError(message) {}
};

class BackendError : public SDRmonError {
public:
    explicit BackendError(const std::string& message) : SDRmonError(message) {}
};

class StreamError : public SDRmonError {
public:
    explicit StreamError(const std::string& message) : SDRmonError(message) {}
};

class ConfigurationError : public SDRmonError {
public:
    explicit ConfigurationError(const std::string& message) : SDRmonError(message) {}
};

class NotSupportedError : public SDRmonError {
public:
    explicit NotSupportedError(const std::string& message) : SDRmonError(message) {}
};

} // namespace sdrmon
