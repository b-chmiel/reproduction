#pragma once

#include <atomic>
#include <cstdio>
#include <string>
namespace tty
{
class PtyLauncher
{
public:
    PtyLauncher(std::string& tty_name);
    PtyLauncher(const PtyLauncher&) = delete;
    PtyLauncher& operator=(const PtyLauncher&) = delete;

    void read_output(const std::atomic<bool>& quit, std::string& output);
    ~PtyLauncher();

private:
    int master_fd;
    int slave_fd;
    char name[BUFSIZ];

    void change_pty_ownership_to_user();
};
}