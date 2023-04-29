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
    PtyLauncher(std::string& tty_name, bool show_output);
    PtyLauncher(const PtyLauncher&) = delete;
    PtyLauncher& operator=(const PtyLauncher&) = delete;

    void read_output(const std::atomic<bool>& quit, std::string& output);

    std::shared_ptr<FileDescriptor> slave;

private:
    std::unique_ptr<FileDescriptor> master;
    char name[BUFSIZ];
    const bool show_output;

    void change_pty_ownership_to_user();
};
}