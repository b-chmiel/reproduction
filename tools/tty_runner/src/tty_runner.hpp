#pragma once

#include "arg.hpp"
#include <string>
#include <string_view>
#include <vector>

namespace tty
{
void run(const tty::arg::Arg&);
bool output_contains(const std::string_view& query);
std::vector<std::string> output_matches(const std::string& regex_pattern);
}