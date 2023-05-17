#include "arg.hpp"
#include <argp.h>
#include <boost/exception/diagnostic_information.hpp>
#include <boost/program_options.hpp>
#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include <cstdlib>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef HAVE_LIBEXPLAIN
#include <libexplain/open.h>
#endif

using namespace std::string_literals;

namespace po = boost::program_options;

using std::_S_in;
using std::cerr;
using std::cout;
using std::getline;
using std::ifstream;
using std::map;
using std::runtime_error;
using std::string;
using std::vector;

enum class Option
{
    HELP,
    PATH_TO_MAKEFILE,
    COMMAND_LIST_SETUP,
    COMMAND_LIST,
    OUTPUT_FILE,
    SHOW_OUTPUT
};

const map<Option, const char*> option_names = {
    { Option::HELP, "help" },
    { Option::PATH_TO_MAKEFILE, "path-to-makefile" },
    { Option::COMMAND_LIST_SETUP, "command-list-setup" },
    { Option::COMMAND_LIST, "command-list" },
    { Option::OUTPUT_FILE, "output-file" },
    { Option::SHOW_OUTPUT, "show-output" }
};

static vector<string> parse_commands(const string& filename)
{
    ifstream file(filename);
    if (not file.is_open())
    {
#ifdef HAVE_LIBEXPLAIN
        throw runtime_error("Could not open file: "s + explain_open(filename.c_str(), O_RDONLY, _S_in));
#else
        throw runtime_error("Could not open file");
#endif
    }

    string line {};
    vector<string> result {};
    while (getline(file, line))
    {
        result.emplace_back(line);
    }

    return result;
}

static vector<string> parse_commands(const string& setup_file, const string& commands_file)
{
    vector<string> setup_commands = parse_commands(setup_file);
    vector<string> commands = parse_commands(commands_file);
    setup_commands.insert(end(setup_commands), begin(commands), end(commands));

    return setup_commands;
}

tty::arg::Arg::Arg(int argc, char* argv[])
{
    po::options_description desc(this->doc.data());

    // clang-format off
  desc.add_options()
	(option_names.at(Option::HELP), "produce help message")
	(option_names.at(Option::PATH_TO_MAKEFILE), po::value<string>()->required(),
      "Path to Makefile of automated vfs project with custom kernel")
	(option_names.at(Option::COMMAND_LIST_SETUP), po::value<string>()->required(),
      "Path to file with setup commands which will be launched before command-list")
	(option_names.at(Option::COMMAND_LIST), po::value<string>()->required(),
      "Path to file with commands that will be executed line-by-line using tty")
	(option_names.at(Option::OUTPUT_FILE), po::value<string>()->default_value(this->output_file),
      "Filename of file with results from commands execution (without "
      "kernel "
      "startup messages)")
    (option_names.at(Option::SHOW_OUTPUT), po::value<bool>()->default_value(this->show_output),
    "Show output in console");
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

    if (vm.count(option_names.at(Option::COMMAND_LIST_SETUP)) && vm.count(option_names.at(Option::COMMAND_LIST)))
    {
        this->command_list_setup_file = vm[option_names.at(Option::COMMAND_LIST_SETUP)].as<string>();
        this->command_list_file = vm[option_names.at(Option::COMMAND_LIST)].as<string>();
        this->commands = parse_commands(this->command_list_setup_file, this->command_list_file);
    }

    if (vm.count(option_names.at(Option::OUTPUT_FILE)))
    {
        this->output_file = vm[option_names.at(Option::OUTPUT_FILE)].as<string>();
    }

    if (vm.count(option_names.at(Option::SHOW_OUTPUT)))
    {
        this->show_output = vm[option_names.at(Option::SHOW_OUTPUT)].as<bool>();
    }
}

tty::arg::Arg::Arg(const string& path_to_makefile, const string& command_list_setup_file, const string& command_list_file, const string& output_file)
    : path_to_makefile(path_to_makefile)
    , command_list_setup_file(command_list_setup_file)
    , command_list_file(command_list_file)
    , output_file(output_file)
    , commands(parse_commands(command_list_setup_file, command_list_file))
    , show_output(false)
{
}