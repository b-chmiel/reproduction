#include "arg.hpp"
#include "fd.hpp"
#include "pty_launcher.hpp"
#include "tty_executor.hpp"
#include "utils.hpp"

#include "tty_runner.hpp"
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <errno.h>
#include <exception>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <pty.h>
#include <signal.h>
#include <stdexcept>
#include <string>
#include <string_view>
#include <sys/ioctl.h>
#include <thread>
#include <unistd.h>
#include <vector>

using namespace std;
using namespace std::this_thread;
using namespace tty;
using namespace tty::arg;
using namespace std::literals;

// https://stackoverflow.com/questions/33237254/how-to-create-pty-that-is-connectable-by-screen-app-in-linux
int main(int argc, char* argv[])
{
    validate_if_run_as_sudo();

    const tty::arg::Arg args(argc, argv);
    if (args.mode == CliMode::HELP)
    {
        return 0;
    }

    cout << args << '\n';

    const auto tty_output = tty::run(args);

    ofstream output(args.output_file);
    output << tty_output;

    return 0;
}
