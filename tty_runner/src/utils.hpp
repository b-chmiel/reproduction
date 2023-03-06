#pragma once

#include <string>
#include <string_view>

namespace tty
{
inline bool string_contains(const std::string_view& s, const std::string_view& other)
{
    return s.find(other) != std::string::npos;
}
}