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

using namespace std::literals;
using std::cout;
using tty::run;
using tty::arg::Arg;
using tty::arg::CliMode;
using tty::utils::validate_if_run_as_sudo;

// https://stackoverflow.com/questions/33237254/how-to-create-pty-that-is-connectable-by-screen-app-in-linux
int main(int argc, char* argv[])
{
    validate_if_run_as_sudo();

    const Arg args(argc, argv);
    if (args.mode == CliMode::HELP)
    {
        return 0;
    }

    cout << args << '\n';

    run(args);
    return 0;
}
