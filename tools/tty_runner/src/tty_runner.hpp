#pragma once

#include "arg.hpp"
#include "fd.hpp"
#include <atomic>
#include <fstream>
#include <memory>
#include <mutex>
#include <string_view>
#include <thread>
#include <vector>

namespace tty
{
class TtyRunner
{
public:
    static std::atomic<bool> quit;
    static std::string tty_output;

    explicit TtyRunner(const tty::arg::Arg&);
    bool output_contains(const std::string_view& query);
    ~TtyRunner()
    {
        std::ofstream output(args.output_file);
        output << tty_output;

        quit = false;
        tty_output = "";
    }

private:
    const tty::arg::Arg args;

    std::string tty_name {};
    std::shared_ptr<FileDescriptor> pty_slave_fd { nullptr };
    std::atomic<bool> tty_launched { false };

    const std::jthread pty;
    const std::jthread killer;
    const std::jthread qemu;
    const std::jthread executor;

    void run_qemu_executor();
    void run_qemu();
    void run_pty();
    void run_pty_killer();
};

void run(const tty::arg::Arg&);
bool output_contains(const std::string_view& query);
}