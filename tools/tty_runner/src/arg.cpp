#include "arg.hpp"
#include <argp.h>
#include <boost/exception/diagnostic_information.hpp>
#include <boost/program_options.hpp>
#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include <cstdlib>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>

using namespace std;
using namespace tty::arg;
namespace po = boost::program_options;

enum class Option
{
    HELP,
    PATH_TO_MAKEFILE,
    COMMAND_LIST,
    OUTPUT_FILE
};

const map<Option, const char*> option_names = {
    { Option::HELP, "help" },
    { Option::PATH_TO_MAKEFILE, "path-to-makefile" },
    { Option::COMMAND_LIST, "command-list" },
    { Option::OUTPUT_FILE, "output-file" }
};

Arg::Arg(int argc, char* argv[])
{
    po::options_description desc(this->doc.data());

    // clang-format off
  desc.add_options()
	(option_names.at(Option::HELP), "produce help message")
	(option_names.at(Option::PATH_TO_MAKEFILE), po::value<string>()->required(),
      "Path to Makefile of automated vfs project with custom kernel")
	(option_names.at(Option::COMMAND_LIST), po::value<string>()->required(),
      "Path to file with commands listed line by line")
	(option_names.at(Option::OUTPUT_FILE), po::value<string>()->default_value(this->output_file),
      "Filename of file with results from commands execution (without "
      "kernel "
      "startup messages)");
    // clang-format on

    po::variables_map vm;
    try
    {
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);
    }
    catch (const boost::exception& ex)
    {
        cerr << boost::diagnostic_information(ex) << '\n';
        cout << desc << '\n';
        this->mode = CliMode::HELP;
        return;
    }

    if (vm.count(option_names.at(Option::HELP)))
    {
        cout << desc << '\n';
        this->mode = CliMode::HELP;
        return;
    }

    if (vm.count(option_names.at(Option::PATH_TO_MAKEFILE)))
    {
        this->path_to_makefile = vm[option_names.at(Option::PATH_TO_MAKEFILE)].as<string>();
    }

    if (vm.count(option_names.at(Option::COMMAND_LIST)))
    {
        this->command_list_file = vm[option_names.at(Option::COMMAND_LIST)].as<string>();
    }

    if (vm.count(option_names.at(Option::OUTPUT_FILE)))
    {
        this->output_file = vm[option_names.at(Option::OUTPUT_FILE)].as<string>();
    }
}