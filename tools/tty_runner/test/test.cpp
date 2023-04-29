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

struct tty_test_Fixture
{
    const tty::arg::Arg args;
    const jthread run;

    tty_test_Fixture()
        : args("../../fs/nilfs-dedup", "commands/dedup.sh", "tty_output_dedup.log")
        , run(tty::run, args)
    {
    }
};

BOOST_TEST_GLOBAL_FIXTURE(tty_test_Fixture);

BOOST_AUTO_TEST_SUITE(dedup_in_memory)

BOOST_AUTO_TEST_CASE(boot_ok)
{
    tty_contains_with_timeout("Starting network: OK", 500ms);
}

BOOST_AUTO_TEST_CASE(verify_before_dedup)
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 0 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", 500ms);
}

BOOST_AUTO_TEST_CASE(dedup)
{
    tty_contains_with_timeout("deduplication succedded, deduplicated", 500ms);
}

BOOST_AUTO_TEST_CASE(verify_after_dedup)
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 1 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", 500ms);
}

BOOST_AUTO_TEST_CASE(verify_after_cat)
{
    tty_contains_with_timeout("CHECKSUM VALIDATION 2 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", 500ms);
}

BOOST_AUTO_TEST_SUITE_END()
