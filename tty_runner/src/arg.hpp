#pragma once

#include <ostream>
#include <string_view>

namespace tty::arg {
enum class CliMode { HELP, NORMAL };

class Arg {
public:
  CliMode mode = CliMode::NORMAL;
  explicit Arg(int argc, char *argv[]);
  friend std::ostream &operator<<(std::ostream &os, const Arg &arg) {
    return os << "ASDF";
  }

private:
  static constexpr std::string_view doc =
      "tty-runner -- program for pseudo terminal automation";

  std::string_view path_to_makefile = "";
  std::string_view command_list_file = "";
  std::string_view output_file = "tty_output.txt";
};
}; // namespace tty::arg