#pragma once

#include "fd.hpp"
#include <atomic>
#include <cstdio>
#include <memory>
#include <string>

namespace tty
{
class PtyLauncher
{
public:
    explicit PtyLauncher(std::string& tty_name, uint verbosity);
    PtyLauncher(const PtyLauncher&) = delete;
    PtyLauncher& operator=(const PtyLauncher&) = delete;

    void read_output(const std::atomic<bool>& quit, std::string& output);

    std::shared_ptr<FileDescriptor> slave;

private:
    std::unique_ptr<FileDescriptor> master;
    char name[BUFSIZ];
    const uint verbosity;

    void change_pty_ownership_to_user();
};
}