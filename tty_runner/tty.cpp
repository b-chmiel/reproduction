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
#include <string>
#include <string_view>
#include <sys/ioctl.h>
#include <thread>
#include <unistd.h>

using namespace std;
using namespace std::this_thread;

static string output;
static string tty_name;

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
        string_view cmd = "c"sv;
        cout << "Cannot execute command: "
             << explain_errno_ioctl(errno, fd, TIOCSTI, (void *)cmd.data())
             << '\n';
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

  cout << "\nAttaching to tty: " << tty_name << '\n';
  Tty tty(tty_name);
  tty.execute("ls");
  tty.execute("\n");
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

// https://stackoverflow.com/questions/33237254/how-to-create-pty-that-is-connectable-by-screen-app-in-linux
int main() {
  validate_if_run_as_sudo();
  setup_signal_handler();
  thread t(act_when_qemu_started);

  int master, slave;
  char name[BUFSIZ];
  const auto e = openpty(&master, &slave, &name[0], nullptr, nullptr);
  if (e < 0) [[unlikely]] {
    printf("Error: %s\n", strerror(errno));
    return -1;
  }

  tty_name = string(name);

  if (not getenv("SUDO_UID")) {
    cout << "Must be run by sudo!\n";
    t.join();
    close(master);
    close(slave);
  }

  const uid_t uid = stoi(getenv("SUDO_UID"));

  fchown(master, uid, uid);
  fchown(slave, uid, uid);

  printf("Slave PTY: %s\n", name);

  int r;
  while (not quit.load() and
         (r = read(master, &name[0], sizeof(name) - 1)) > 0) {
    name[r] = '\0';
    const string_view line(&name[0]);
    output += line;
    printf("%s", line.data());
  }

  cout << "Cleanup" << '\n';
  t.join();
  close(slave);
  close(master);

  return 0;
}
