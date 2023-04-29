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

using namespace std;
using namespace std::this_thread;
using namespace tty::arg;
using namespace tty;
using namespace std::literals;

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

void run_qemu_executor(const vector<string>& commands)
{
    cout << "Launched " << __func__ << " thread\n";

    tty_launched.wait(false);

    sleep_for(3s);

    while (not quit.load() and not string_contains(tty_output, "Starting network: OK"sv))
    {
        sleep_for(1s);
    }

    if (quit.load())
    {
        return;
    }

    TtyExecutor tty(tty_name);
    cout << "\nAttached to tty: " << tty_name << '\n';

    if (commands.empty())
    {
        throw runtime_error("Commands empty!");
    }

    for (const auto& cmd : commands)
    {
        tty.execute(cmd + "\n");
    }

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

    quit.store(true);
    quit.notify_all();
}

void run_pty()
{
    cout << "Launched " << __func__ << " thread\n";

    PtyLauncher pty(tty_name);
    tty_launched.store(true);
    tty_launched.notify_all();
    pty_slave_fd = pty.slave;

    pty.read_output(quit, tty_output);

    cout << "Stopped " << __func__ << " thread\n";
    quit.store(true);
    quit.notify_all();
}

void run_pty_killer()
{
    tty_launched.wait(false);
    quit.wait(false);
    cout << "Starting pty kill\n";

    // unfortunately slave_fd destructor is not called
    // so manual deletion is required.

    close(pty_slave_fd->fd);
}

bool tty::output_contains(const string_view& query)
{
    return string_contains(tty_output, query);
}

bool tty::is_running()
{
    return !quit.load();
}

string tty::run(const tty::arg::Arg& args)
{
    setup_signal_handler();

    jthread pty(run_pty);
    jthread killer(run_pty_killer);
    jthread qemu(run_qemu, args.path_to_makefile);
    jthread executor(run_qemu_executor, args.commands);

    return tty_output;
}
