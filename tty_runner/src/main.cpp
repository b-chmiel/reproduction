#include "arg.hpp"
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <errno.h>
#include <fcntl.h>
#include <iostream>
#include <libexplain/ioctl.h>
#include <libexplain/libexplain.h>
#include <pty.h>
#include <signal.h>
#include <stdexcept>
#include <string>
#include <string_view>
#include <sys/ioctl.h>
#include <thread>
#include <unistd.h>

using namespace std;
using namespace std::this_thread;
using namespace tty::arg;

static string output;
static string tty_name = "";

atomic<bool> quit(false);

inline bool string_contains(const string_view &s, const string_view &other) {
  return s.find(other) != string::npos;
}

class Tty {
public:
  explicit Tty(const string &name) : name(name) {
    fd = open(this->name.data(), O_RDWR);

    if (fd < 0) [[unlikely]] {
      cout << "Cannot open file: " << strerror(errno) << '\n';
    }
  }

  void execute(const string &command) {
    for (char ch : command) {
      const int result = ioctl(fd, TIOCSTI, &ch);

      if (result < 0) [[unlikely]] {
#ifdef HAVE_LIBEXPLAIN
        cout << "Cannot execute command: "
             << explain_errno_ioctl(errno, fd, TIOCSTI, &ch) << '\n';
#else
        cout << "Cannot execute command: " << strerror(errno) << '\n';
#endif
      }
    }
  }

  ~Tty() { close(fd); }

private:
  const string_view name;
  int fd;
};

void act_when_qemu_started() {
  using namespace std::literals;

  sleep_for(3s);

  while (not quit.load() and
         not string_contains(output, "Starting network: OK"sv)) {
    sleep_for(1s);
  }

  if (quit.load()) {
    return;
  }

  cout << "\nAttaching to tty: " << tty_name << '\n';
  if (tty_name == "") {
    throw runtime_error("tty_name not set by Pty");
  }

  Tty tty(tty_name);
  tty.execute("ls\n");
  tty.execute("exit\n");
}

void sigint_handler(int) { quit.store(true); }

void setup_signal_handler() {
  struct sigaction sa;
  memset(&sa, 0, sizeof(sa));
  sa.sa_handler = sigint_handler;
  sigfillset(&sa.sa_mask);
  sigaction(SIGINT, &sa, NULL);
}

void validate_if_run_as_sudo() {
  const auto me = getuid();
  const auto privileges = geteuid();

  if (me != privileges) {
    cout << "Must be run by sudo!\n";
    exit(EXIT_FAILURE);
  }
}

class Pty {
public:
  Pty() {
    const auto e = openpty(&master_fd, &slave_fd, &name[0], nullptr, nullptr);
    if (e < 0) [[unlikely]] {
      throw runtime_error(strerror(errno));
    }

    tty_name = string(name);
    cout << "Slave PTY: " << tty_name << '\n';

    change_pty_ownership_to_user();
  }

  void read_output() {
    int r;
    while (not quit.load() and
           (r = read(master_fd, &name[0], sizeof(name) - 1)) > 0) {
      name[r] = '\0';
      const string_view line(&name[0]);
      output += line;
      printf("%s", line.data());
    }
  }

  ~Pty() {
    close(master_fd);
    close(slave_fd);
  }

private:
  int master_fd;
  int slave_fd;
  char name[BUFSIZ];

  void change_pty_ownership_to_user() {
    if (not getenv("SUDO_UID")) {
      throw runtime_error("Must be run by sudo!");
    }

    const uid_t uid = stoi(getenv("SUDO_UID"));

    fchown(master_fd, uid, uid);
    fchown(slave_fd, uid, uid);
  }
};

// https://stackoverflow.com/questions/33237254/how-to-create-pty-that-is-connectable-by-screen-app-in-linux
int main(int argc, char *argv[]) {
  validate_if_run_as_sudo();
  setup_signal_handler();

  tty::arg::Arg args(argc, argv);
  cout << args << '\n';
  if (args.mode == CliMode::HELP) {
    return 0;
  }

  thread t(act_when_qemu_started);

  Pty pty;
  pty.read_output();

  cout << "Cleanup\n";
  t.join();

  return 0;
}
