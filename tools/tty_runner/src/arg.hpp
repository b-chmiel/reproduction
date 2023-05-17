#pragma once

#include <ostream>
#include <string>
#include <string_view>
#include <syslog.h>
#include <vector>

namespace tty::arg
{
enum class CliMode
{
    HELP,
    NORMAL
};

class Arg
{
public:
    std::vector<std::string> commands {};

    CliMode mode = CliMode::NORMAL;
    std::string path_to_makefile = "";
    std::string command_list_setup_file = "";
    std::string command_list_file = "";
    std::string output_file = "tty_output.txt";
    uint verbosity = LOG_INFO;

    explicit Arg(int argc, char* argv[]);
    explicit Arg(const std::string& path_to_makefile, const std::string& command_list_setup_file, const std::string& command_list_file, const std::string& output_file);

    friend std::ostream& operator<<(std::ostream& os, const Arg& arg)
    {
        return os << "Args:\n"
                  << "path_to_makefile = " << arg.path_to_makefile << '\n'
                  << "command_list_setup_file = " << arg.command_list_setup_file << '\n'
                  << "command_list_file = " << arg.command_list_file << '\n'
                  << "output_file = " << arg.output_file << '\n'
                  << "verbosity = " << arg.verbosity << '\n';
    }

private:
    static constexpr std::string_view doc = "tty-runner -- program for pseudo terminal automation";
};
}; // namespace tty::arg