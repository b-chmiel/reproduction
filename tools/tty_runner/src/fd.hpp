#pragma once

#include <iostream>
#include <sys/syslog.h>
#include <unistd.h>

namespace tty
{
class FileDescriptor
{
public:
    const int fd;
    const uint verbosity;
    explicit FileDescriptor(int fd, uint verbosity)
        : fd(fd)
        , verbosity(verbosity) {};

    FileDescriptor(const FileDescriptor&) = delete;
    FileDescriptor& operator=(const FileDescriptor&) = delete;

    ~FileDescriptor()
    {
        if (verbosity >= LOG_INFO)
            std::cout << "Closing fd: " << fd << "\n";

        ::close(fd);
    }
};
}