#define BOOST_TEST_MODULE tty_test
#include "tty_runner.hpp"
#include <boost/test/unit_test_suite.hpp>

#include <boost/test/included/unit_test.hpp>
#include <chrono>
#include <stdexcept>
#include <string_view>
#include <thread>
#include <unistd.h>

using namespace std;
using namespace std::this_thread;
using namespace std::chrono_literals;

void tty_contains_with_timeout(const std::string& query, const chrono::milliseconds timeout)
{
    uint retries = 0;
    const uint max_retries = 50;
    while (retries++ < max_retries)
    {
        if (tty::output_contains(query))
        {
            BOOST_TEST(true);
            return;
        }

        sleep_for(timeout);
    }

    BOOST_TEST(false);
}

struct Fixture
{
    const tty::arg::Arg args;
    const jthread run;

    Fixture()
        : args("../../fs/nilfs-dedup", "commands/dedup.sh", "tty_output_dedup.log")
        , run(tty::run, args)
    {
    }
};

BOOST_TEST_GLOBAL_FIXTURE(Fixture);

BOOST_AUTO_TEST_CASE(deduplication_in_memory_boot_ok)
{
    tty_contains_with_timeout("Starting network: OK", 500ms);
}

BOOST_AUTO_TEST_CASE(deduplication_in_memory_verify_before_dedup)
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 0 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", 500ms);
}

BOOST_AUTO_TEST_CASE(deduplication_in_memory_dedup)
{
    tty_contains_with_timeout("deduplication succedded, deduplicated", 500ms);
}

BOOST_AUTO_TEST_CASE(deduplication_in_memory_verify_after_dedup)
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 1 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", 500ms);
}

BOOST_AUTO_TEST_CASE(deduplication_in_memory_verify_after_cat)
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 2 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", 500ms);
}