#include <iostream>
#define BOOST_TEST_MODULE dedup
#include "tty_runner.hpp"

#include <boost/test/included/unit_test.hpp>
#include <boost/test/unit_test_suite.hpp>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unistd.h>

// namespace utf = boost::unit_test;

using namespace std::chrono_literals;

namespace fs = std::filesystem;

using std::jthread;
using std::make_unique;
using std::string;
using std::unique_ptr;
using std::chrono::milliseconds;
using std::this_thread::sleep_for;

constexpr auto path_to_dedup = "../../fs/nilfs-dedup";
constexpr auto output_path = "../../fs/nilfs-dedup/out/tty_runner";
constexpr auto timeout = 200ms;

struct FixtureDedupInMemory
{
    const tty::arg::Arg args;
    const jthread run;

    FixtureDedupInMemory()
        : args(path_to_dedup, "commands/setup.sh", "commands/generate.sh", "test_tty_output_generate.log")
        , run(tty::run, args)
    {
    }
};

struct FixtureDedupedAfterUmount
{
    const tty::arg::Arg args;
    const jthread run;

    FixtureDedupedAfterUmount()
        : args(path_to_dedup, "commands/setup.sh", "commands/dedup.sh", "test_tty_output_remount.log")
        , run(tty::run, args)
    {
    }
};

static unique_ptr<FixtureDedupInMemory> dedup_in_memory_fixture;
static unique_ptr<FixtureDedupedAfterUmount> deduped_after_umount_fixture;

static void tty_contains(const string& query, const milliseconds timeout)
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

static bool file_contains(const string& file_path, const string& content)
{
    std::ifstream file(file_path);
    string file_content {};
    string line {};

    while (std::getline(file, line))
    {
        file_content += line;
    }

    return file_content.find(content) != string::npos;
}

static void validate_file_contains(const string& file_path, const string& content, const milliseconds timeout)
{
    const uint max_retries = 50;
    uint retries = 0;
    while (retries++ < max_retries)
    {
        if (fs::exists(file_path) && file_contains(file_path, content))
        {
            BOOST_TEST(true);
            return;
        }

        sleep_for(timeout);
    }

    BOOST_TEST(false);
}

BOOST_AUTO_TEST_SUITE(generate)

constexpr auto suite_dir = "/generate";
const string path = string(output_path) + suite_dir;

BOOST_AUTO_TEST_CASE(setup)
{
    dedup_in_memory_fixture = make_unique<FixtureDedupInMemory>();
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_CASE(boot_ok)
{
    tty_contains("Running sysctl", timeout);
    tty_contains("Starting network", timeout);
}

BOOST_AUTO_TEST_CASE(tty_initialized)
{
    validate_file_contains(path + "/started", "1", timeout);
}

// BOOST_AUTO_TEST_CASE(verify_before_gen)
// {
//     // validate_file_has_content(path_to_dedup + "/out/generate/validate_0_checksum_f1", "/mnt/nilfs2/f1: FAILED", timeout);
//     BOOST_TEST(true);
// }

// BOOST_AUTO_TEST_CASE(dedup)
// {
//     tty_contains("deduplication succedded, deduplicated", timeout);
// }

// BOOST_AUTO_TEST_CASE(verify_after_dedup)
// {
//     tty_contains("CHECKSUM VALIDATION 1 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", timeout);
// }

// BOOST_AUTO_TEST_CASE(verify_after_cat)
// {
//     tty_contains("CHECKSUM VALIDATION 2 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", timeout);
// }

// BOOST_AUTO_TEST_CASE(poweroff)
// {
//     tty_contains("reboot: machine restart", timeout);
// }

BOOST_AUTO_TEST_CASE(teardown)
{
    dedup_in_memory_fixture.reset();
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_SUITE_END()

// BOOST_AUTO_TEST_SUITE(deduped_after_umount)
// BOOST_AUTO_TEST_CASE(setup, *utf::depends_on("dedup_in_memory/teardown"))
// {
//     deduped_after_umount_fixture = make_unique<FixtureDedupedAfterUmount>();
//     BOOST_TEST(true);
// }
// BOOST_AUTO_TEST_CASE(boot_ok, *utf::depends_on("dedup_in_memory/teardown"))
// {
//     tty_contains("Running sysctl", timeout);
//     tty_contains("Starting network", timeout);
// }

// BOOST_AUTO_TEST_CASE(verify_before_cat, *utf::depends_on("dedup_in_memory/teardown"))
// {
//     tty_contains("CHECKSUM VALIDATION 0 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", timeout);
// }

// BOOST_AUTO_TEST_CASE(verify_after_cat, *utf::depends_on("dedup_in_memory/teardown"))
// {
//     tty_contains("CHECKSUM VALIDATION 1 /mnt/nilfs2/f1: OK /mnt/nilfs2/f2: OK", timeout);
// }

// BOOST_AUTO_TEST_CASE(poweroff, *utf::depends_on("dedup_in_memory/teardown"))
// {
//     tty_contains("reboot: machine restart", timeout);
// }
// BOOST_AUTO_TEST_CASE(teardown, *utf::depends_on("dedup_in_memory/teardown"))
// {
//     deduped_after_umount_fixture.reset();
//     BOOST_TEST(true);
// }
// BOOST_AUTO_TEST_SUITE_END()