#pragma once

#include "arg.hpp"
#include <string_view>
#include <vector>

namespace tty
{
std::string run(const tty::arg::Arg&);
bool output_contains(const std::string_view& query);
}