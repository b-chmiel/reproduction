#define BOOST_TEST_MODULE dedup
#include "test_utils.hpp"
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
using namespace test;

namespace utf = boost::unit_test;

struct FixtureDedupInMemory
{
    const tty::arg::Arg args;
    const jthread run;

    FixtureDedupInMemory()
        : args("../../fs/nilfs-dedup", "commands/dedup.sh", "tty_output_dedup.log")
        , run(tty::run, args)
    {
    }
};

struct FixtureDedupedAfterUmount
{
    const tty::arg::Arg args;
    const jthread run;

    FixtureDedupedAfterUmount()
        : args("../../fs/nilfs-dedup", "commands/remount.sh", "tty_output_remount.log")
        , run(tty::run, args)
    {
    }
};

constexpr std::chrono::milliseconds timeout = 200ms;

static unique_ptr<FixtureDedupInMemory> dedup_in_memory_fixture;
static unique_ptr<FixtureDedupedAfterUmount> deduped_after_umount_fixture;

BOOST_AUTO_TEST_SUITE(dedup_in_memory)
BOOST_AUTO_TEST_CASE(setup)
{
    dedup_in_memory_fixture = make_unique<FixtureDedupInMemory>();
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_CASE(boot_ok)
{
    tty_contains_with_timeout("Starting network: OK", timeout);
}

BOOST_AUTO_TEST_CASE(verify_before_dedup)
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 0 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(dedup)
{
    tty_contains_with_timeout("deduplication succedded, deduplicated", timeout);
}

BOOST_AUTO_TEST_CASE(verify_after_dedup)
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 1 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(verify_after_cat)
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 2 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(poweroff)
{
    tty_contains_with_timeout("reboot: machine restart", timeout);
}

BOOST_AUTO_TEST_CASE(teardown)
{
    dedup_in_memory_fixture.reset();
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(deduped_after_umount)
BOOST_AUTO_TEST_CASE(setup, *utf::depends_on("dedup_in_memory/teardown"))
{
    deduped_after_umount_fixture = make_unique<FixtureDedupedAfterUmount>();
    BOOST_TEST(true);
}
BOOST_AUTO_TEST_CASE(boot_ok, *utf::depends_on("dedup_in_memory/teardown"))
{
    tty_contains_with_timeout("Starting network: OK", timeout);
}

BOOST_AUTO_TEST_CASE(verify_before_cat, *utf::depends_on("dedup_in_memory/teardown"))
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 0 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(verify_after_cat, *utf::depends_on("dedup_in_memory/teardown"))
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 1 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(poweroff, *utf::depends_on("dedup_in_memory/teardown"))
{
    tty_contains_with_timeout("reboot: machine restart", timeout);
}
BOOST_AUTO_TEST_CASE(teardown, *utf::depends_on("dedup_in_memory/teardown"))
{
    deduped_after_umount_fixture.reset();
    BOOST_TEST(true);
}
BOOST_AUTO_TEST_SUITE_END()