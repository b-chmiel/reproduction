#pragma once

#include <boost/process.hpp>
#include <boost/process/io.hpp>
#include <boost/process/pipe.hpp>
#include <boost/process/search_path.hpp>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unistd.h>

namespace bp = boost::process;

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

inline std::string execute_command(const std::string& cmd)
{
    bp::ipstream out;
    bp::child c(bp::search_path("zsh"), cmd, bp::std_out > out);
    c.wait();

    std::string result {};
    std::string line {};

    while (std::getline(out, line))
        result += line;

    return result;
}
}