#include "arg.hpp"
#include "fd.hpp"
#include "pty_launcher.hpp"
#include "tty_executor.hpp"
#include "utils.hpp"

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <errno.h>
#include <exception>
#include <fcntl.h>
#include <iostream>
#include <libexplain/ioctl.h>
#include <libexplain/libexplain.h>
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

using namespace std;
using namespace std::this_thread;
using namespace tty;
using namespace tty::arg;
using namespace std::literals;

string output;
string tty_name = "";
mutex tty_name_mutex;
shared_ptr<FileDescriptor> slave_fd;

atomic<bool> quit(false);
atomic<bool> tty_launched(false);

void run_qemu_executor()
{
    cout << "Launched " << __func__ << " thread\n";

    tty_launched.wait(false);

    sleep_for(3s);

    while (not quit.load() and not string_contains(output, "Starting network: OK"sv))
    {
        sleep_for(1s);
    }

    if (quit.load())
    {
        return;
    }

    TtyExecutor tty(tty_name);
    cout << "\nAttached to tty: " << tty_name << '\n';

    tty.execute("ls\n");
    tty.execute("reboot\n");

    cout << "Stopped " << __func__ << " thread\n";
    quit.store(true);
    quit.notify_all();
}

void run_qemu(const string& makefile_path)
{
    cout << "Launched " << __func__ << " thread\n";

    tty_launched.wait(false);

    cout << "Launching qemu instance\n";

    const string command = "SERIAL_TTY=" + tty_name + " make -C " + makefile_path + " vm-tty ";
    system(command.c_str());

    cout << "Stopped qemu instance\n";
}

void run_pty()
{
    cout << "Launched " << __func__ << " thread\n";

    PtyLauncher pty(tty_name);
    tty_launched.store(true);
    tty_launched.notify_all();
    slave_fd = pty.slave;

    pty.read_output(quit, output);

    cout << "Stopped " << __func__ << " thread\n";
}

void run_pty_killer()
{
    tty_launched.wait(false);
    quit.wait(false);
    cout << "Starting pty kill\n";

    // unfortunately slave_fd destructor is not called
    // so manual deletion is required.

    close(slave_fd->fd);
    slave_fd.reset();
}

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

// https://stackoverflow.com/questions/33237254/how-to-create-pty-that-is-connectable-by-screen-app-in-linux
int main(int argc, char* argv[])
{
    validate_if_run_as_sudo();
    setup_signal_handler();

    tty::arg::Arg args(argc, argv);
    if (args.mode == CliMode::HELP)
    {
        return 0;
    }

    cout << args << '\n';

    thread pty(run_pty);
    thread killer(run_pty_killer);
    thread qemu(run_qemu, args.path_to_makefile);
    thread executor(run_qemu_executor);

    pty.join();
    killer.join();
    qemu.join();
    executor.join();

    return 0;
}
