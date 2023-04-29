#include "catch2/catch_message.hpp"
#include "tty_runner.hpp"
#include <catch2/catch_test_macros.hpp>
#include <chrono>
#include <stdexcept>
#include <string_view>
#include <thread>
#include <unistd.h>

using namespace std;
using namespace std::this_thread;
using namespace std::chrono_literals;

string bool_to_string(bool b)
{
    return b ? "true" : "false";
}

void tty_contains_with_timeout(const std::string& query, const chrono::milliseconds timeout)
{
    uint retries = 0;
    const uint max_retries = 50;
    while (tty::is_running() && retries++ < max_retries)
    {
        if (tty::output_contains(query))
        {
            CHECK(true);
            return;
        }

        sleep_for(timeout);
    }

    WARN("Contains query timeout. Reason: is_running="s + bool_to_string(tty::is_running()) + " retries="s + to_string(retries));

    REQUIRE(false);
}

class Fixture
{
private:
    const tty::arg::Arg args;
    const jthread run;

public:
    Fixture()
        : args("../../fs/nilfs-dedup", "commands/dedup.sh", "tty_output_dedup.log")
        , run(tty::run, args)
    {
    }
};

Fixture fixture;

TEST_CASE("deduplication in-memory - boot ok")
{
    // SECTION("boot ok")
    // {
    tty_contains_with_timeout("Starting network: OK", 500ms);
}
TEST_CASE("asdf")
{
    // }

    // SECTION("validation before dedup")
    // {
    tty_contains_with_timeout("CHECKSUM VALIDATION 0 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", 500ms);
    // }
}
