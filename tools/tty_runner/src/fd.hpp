#pragma once

#include <iostream>
#include <unistd.h>

namespace tty
{
class FileDescriptor
{
public:
    const int fd;
    explicit FileDescriptor(int fd)
        : fd(fd) {};

    FileDescriptor(const FileDescriptor&) = delete;
    FileDescriptor& operator=(const FileDescriptor&) = delete;

    ~FileDescriptor()
    {
        std::cout << "Closing fd: " << fd << "\n";
        close(fd);
    }
};
}