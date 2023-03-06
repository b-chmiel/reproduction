#pragma once

#include <string>
#include <string_view>

namespace tty
{
class TtyExecutor
{
public:
    explicit TtyExecutor(const std::string& name);

    TtyExecutor(const TtyExecutor&) = delete;
    TtyExecutor& operator=(const TtyExecutor&) = delete;

    void execute(const std::string& command);
    ~TtyExecutor();

private:
    const std::string_view name;
    int fd;
};
}