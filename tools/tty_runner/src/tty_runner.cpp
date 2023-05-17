#include "tty_runner.hpp"
#include <iostream>
#include <thread>

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

using std::atomic;
using std::cout;
using std::jthread;
using std::mutex;
using std::ofstream;
using std::runtime_error;
using std::shared_ptr;
using std::string;
using std::string_view;
using std::this_thread::sleep_for;

using tty::FileDescriptor;
using tty::PtyLauncher;
using tty::TtyExecutor;
using tty::arg::Arg;

string tty_output;
string tty_name = "";
mutex tty_name_mutex;
shared_ptr<FileDescriptor> pty_slave_fd;

atomic<bool> quit(false);
atomic<bool> tty_launched(false);

void sigint_handler(int)
{
    quit.store(true);
}

void setup_signal_handler()
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = sigint_handler;
    sigfillset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);
}

void run_qemu_executor(const Arg& arg)
{
    if (arg.verbosity >= LOG_INFO)
        cout << "Launched " << __func__ << " thread\n";

    tty_launched.wait(false);

    sleep_for(3s);

    while (not quit.load() and not tty::utils::string_contains(tty_output, "Starting network: OK"sv))
    {
        sleep_for(1s);
    }

    if (quit.load())
    {
        return;
    }

    TtyExecutor tty(tty_name);

    if (arg.verbosity >= LOG_INFO)
        cout << "\nAttached to tty: " << tty_name << '\n';

    if (arg.commands.empty())
    {
        throw runtime_error("Commands empty!");
    }

    for (const auto& cmd : arg.commands)
    {
        tty.execute(cmd + "\n");
    }

    tty.execute("reboot\n");

    if (arg.verbosity >= LOG_INFO)
        cout << "Stopped " << __func__ << " thread\n";

    quit.store(true);
    quit.notify_all();
}

void run_qemu(const Arg& arg)
{
    if (arg.verbosity >= LOG_INFO)
        cout << "Launched " << __func__ << " thread\n";

    tty_launched.wait(false);

    if (arg.verbosity >= LOG_INFO)
        cout << "Launching qemu instance\n";

    const string command = "SERIAL_TTY=" + tty_name + " make -C " + arg.path_to_makefile + " vm-tty ";
    const auto output = tty::utils::exec(command.c_str());

    if (arg.verbosity >= LOG_DEBUG)
        cout << output;

    if (arg.verbosity >= LOG_INFO)
        cout << "Stopped qemu instance\n";

    quit.store(true);
    quit.notify_all();
}

void run_pty(const Arg& arg)
{
    if (arg.verbosity >= LOG_INFO)
        cout << "Launched " << __func__ << " thread\n";

    PtyLauncher pty(tty_name, arg.verbosity);
    tty_launched.store(true);
    tty_launched.notify_all();
    pty_slave_fd = pty.slave;

    pty.read_output(quit, tty_output);

    if (arg.verbosity >= LOG_INFO)
        cout << "Stopped " << __func__ << " thread\n";

    quit.store(true);
    quit.notify_all();
}

void run_pty_killer(const Arg& arg)
{
    tty_launched.wait(false);
    quit.wait(false);

    if (arg.verbosity >= LOG_INFO)
        cout << "Starting pty kill\n";

    // unfortunately slave_fd destructor is not called
    // so manual deletion is required.

    ::close(pty_slave_fd->fd);
}

bool tty::output_contains(const string_view& query)
{
    return tty::utils::string_contains(tty_output, query);
}

void tty::run(const Arg& args)
{
    tty_output = "";
    tty_name = "";
    pty_slave_fd = { nullptr };
    quit = false;
    tty_launched = false;

    setup_signal_handler();

    {
        jthread pty(run_pty, args);
        jthread killer(run_pty_killer, args);
        jthread qemu(run_qemu, args);
        jthread executor(run_qemu_executor, args);
    }

    ofstream output(args.output_file);
    output << tty_output;
}
