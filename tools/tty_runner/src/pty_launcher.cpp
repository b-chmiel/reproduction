#include "pty_launcher.hpp"
#include "fd.hpp"
#include <atomic>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <memory>
#include <pty.h>
#include <stdexcept>
#include <string>
#include <sys/select.h>
#include <sys/syslog.h>
#include <unistd.h>

using namespace tty;
using std::atomic;
using std::cout;
using std::make_shared;
using std::make_unique;
using std::runtime_error;
using std::stoi;
using std::string;
using std::string_view;

PtyLauncher::PtyLauncher(string& tty_name, uint verbosity)
    : verbosity(verbosity)
{
    int master_fd, slave_fd;

    const auto e = openpty(&master_fd, &slave_fd, &name[0], nullptr, nullptr);
    if (e < 0) [[unlikely]]
    {
        throw runtime_error(strerror(errno));
    }

    master = make_unique<FileDescriptor>(master_fd, verbosity);
    slave = make_shared<FileDescriptor>(slave_fd, verbosity);

    tty_name = string(name);

    if (verbosity >= LOG_INFO)
        cout << "Slave PTY: " << tty_name << '\n';

    change_pty_ownership_to_user();
}

void PtyLauncher::read_output(const atomic<bool>& quit, string& output)
{
    int r;
    while ((r = read(master.get()->fd, &name[0], sizeof(name) - 1)) > 0)
    {
        name[r] = '\0';
        const string_view line(&name[0]);
        output += line;

        if (verbosity >= LOG_DEBUG)
        {
            printf("%s", line.data());
        }
    }
}

void PtyLauncher::change_pty_ownership_to_user()
{
    if (not getenv("SUDO_UID"))
    {
        throw runtime_error("Must be run by sudo!");
    }

    const uid_t uid = stoi(getenv("SUDO_UID"));

    fchown(master.get()->fd, uid, uid);
    fchown(slave.get()->fd, uid, uid);
}