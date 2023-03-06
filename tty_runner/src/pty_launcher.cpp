#include "pty_launcher.hpp"
#include <atomic>
#include <cerrno>
#include <cstring>
#include <iostream>
#include <pty.h>
#include <stdexcept>
#include <string>
#include <unistd.h>

using namespace std;
using namespace tty;

PtyLauncher::PtyLauncher(string& tty_name)
{
    const auto e = openpty(&master_fd, &slave_fd, &name[0], nullptr, nullptr);
    if (e < 0) [[unlikely]]
    {
        throw runtime_error(strerror(errno));
    }

    tty_name = string(name);
    cout << "Slave PTY: " << tty_name << '\n';

    change_pty_ownership_to_user();
}

void PtyLauncher::read_output(const atomic<bool>& quit, string& output)
{
    int r;
    while (not quit.load() and (r = read(master_fd, &name[0], sizeof(name) - 1)) > 0)
    {
        name[r] = '\0';
        const string_view line(&name[0]);
        output += line;
        printf("%s", line.data());
    }
}

PtyLauncher::~PtyLauncher()
{
    close(master_fd);
    close(slave_fd);
}

void PtyLauncher::change_pty_ownership_to_user()
{
    if (not getenv("SUDO_UID"))
    {
        throw runtime_error("Must be run by sudo!");
    }

    const uid_t uid = stoi(getenv("SUDO_UID"));

    fchown(master_fd, uid, uid);
    fchown(slave_fd, uid, uid);
}