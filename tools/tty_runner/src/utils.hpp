#pragma once

#include <array>
#include <cstdio>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unistd.h>

namespace tty::utils
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

inline std::string exec(const char* cmd)
{
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
    if (!pipe)
    {
        throw std::runtime_error("popen() failed!");
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr)
    {
        result += buffer.data();
    }
    return result;
}
}