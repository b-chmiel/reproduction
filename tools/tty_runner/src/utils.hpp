#pragma once

#include <stdexcept>
#include <string>
#include <string_view>
#include <unistd.h>

namespace tty
{
inline bool string_contains(const std::string_view& s, const std::string_view& other)
{
    return s.find(other) != std::string::npos;
}

inline void validate_if_run_as_sudo()
{
    if (::getuid() != 0)
    {
        throw std::runtime_error("This program must be run by sudo!");
    }
}
}