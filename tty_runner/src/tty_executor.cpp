#include "tty_executor.hpp"
#include <asm-generic/ioctls.h>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <libexplain/ioctl.h>
#include <sys/ioctl.h>
#include <unistd.h>

using namespace tty;
using namespace std;

TtyExecutor::TtyExecutor(const string& tty_name)
    : name(tty_name)
{
    fd = open(this->name.data(), O_RDWR);

    if (fd < 0) [[unlikely]]
    {
        cout << "Cannot open file: " << strerror(errno) << '\n';
    }
}

void TtyExecutor::execute(const string& command)
{
    for (char ch : command)
    {
        const int result = ioctl(fd, TIOCSTI, &ch);

        if (result < 0) [[unlikely]]
        {
#ifdef HAVE_LIBEXPLAIN
            cout << "Cannot execute command: "
                 << explain_errno_ioctl(errno, fd, TIOCSTI, &ch) << '\n';
#else
            cout << "Cannot execute command: " << strerror(errno) << '\n';
#endif
        }
    }
}

TtyExecutor::~TtyExecutor() { close(fd); }
