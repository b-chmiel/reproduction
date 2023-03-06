#include "arg.hpp"
#include "pty_launcher.hpp"
#include "tty_executor.hpp"
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <errno.h>
#include <fcntl.h>
#include <iostream>
#include <libexplain/ioctl.h>
#include <libexplain/libexplain.h>
#include <pty.h>
#include <signal.h>
#include <stdexcept>
#include <string>
#include <string_view>
#include <sys/ioctl.h>
#include <thread>
#include <unistd.h>

using namespace std;
using namespace std::this_thread;
using namespace tty;
using namespace tty::arg;

static string output;
static string tty_name = "";

atomic<bool> quit(false);

inline bool string_contains(const string_view& s, const string_view& other)
{
    return s.find(other) != string::npos;
}

void act_when_qemu_started()
{
    using namespace std::literals;

    sleep_for(3s);

    while (not quit.load() and not string_contains(output, "Starting network: OK"sv))
    {
        sleep_for(1s);
    }

    if (quit.load())
    {
        return;
    }

    cout << "\nAttaching to tty: " << tty_name << '\n';
    if (tty_name == "")
    {
        throw runtime_error("tty_name not set by Pty");
    }

    TtyExecutor tty(tty_name);
    tty.execute("ls\n");
    tty.execute("exit\n");
}

void sigint_handler(int) { quit.store(true); }

void setup_signal_handler()
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = sigint_handler;
    sigfillset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);
}

void validate_if_run_as_sudo()
{
    const auto me = getuid();
    const auto privileges = geteuid();

    if (me != privileges)
    {
        cout << "Must be run by sudo!\n";
        exit(EXIT_FAILURE);
    }
}

void run_qemu(const string& makefile_path, const string& pty_name)
{
    const string command = "SERIAL_TTY=" + pty_name + " make -C " + makefile_path + " vm-tty ";
    cout << "Launching qemu instance\n";
    system(command.c_str());
}

// https://stackoverflow.com/questions/33237254/how-to-create-pty-that-is-connectable-by-screen-app-in-linux
int main(int argc, char* argv[])
{
    validate_if_run_as_sudo();
    setup_signal_handler();

    tty::arg::Arg args(argc, argv);
    cout << args << '\n';
    if (args.mode == CliMode::HELP)
    {
        return 0;
    }

    PtyLauncher pty(tty_name);
    pty.read_output(quit, output);
    // TODO launch this on separate thread

    thread qemu(run_qemu, args.path_to_makefile, tty_name);
    // thread executor(act_when_qemu_started);

    cout << "Cleanup\n";
    qemu.join();
    // executor.join();

    return 0;
}
