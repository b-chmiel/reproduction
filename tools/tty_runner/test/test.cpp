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
namespace utf = boost::unit_test;

using std::ifstream;
using std::jthread;
using std::make_unique;
using std::string;
using std::unique_ptr;
using std::chrono::milliseconds;
using std::this_thread::sleep_for;

constexpr auto path_to_dedup = "../../fs/nilfs-dedup";
const auto output_path = string(path_to_dedup) + "/out/tty_runner";
constexpr auto timeout = 200ms;

struct Fixture
{
    const tty::arg::Arg args;
    const jthread run;

    explicit Fixture(const string& setup_file, const string& commands_file, const string& log_file)
        : args(path_to_dedup, setup_file, commands_file, log_file)
        , run(tty::run, args)
    {
    }
};

static void validate_tty_contains(const string& query, const milliseconds timeout)
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

static void check_file_content_equals(const string& file_path, const string& content)
{
    ifstream file(file_path);
    string file_content {};
    string line {};

    while (std::getline(file, line))
    {
        file_content += line;
    }

    BOOST_TEST(file_content == content);
}

static void validate_file_equals(const string& file_path, const string& content, const milliseconds timeout)
{
    const uint max_retries = 50;
    uint retries = 0;
    while (retries++ < max_retries)
    {
        if (fs::exists(file_path))
        {
            check_file_content_equals(file_path, content);
            return;
        }

        sleep_for(timeout);
    }

    BOOST_TEST(false);
    assert(false);
}

BOOST_AUTO_TEST_SUITE(generate)

constexpr auto suite_dir = "/generate";
const string path = string(output_path) + suite_dir;

unique_ptr<Fixture> fixture;

BOOST_AUTO_TEST_CASE(setup)
{
    fixture = make_unique<Fixture>("commands/setup.sh", "commands/generate.sh", "test_tty_output_generate.log");
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_CASE(boot_ok)
{
    validate_tty_contains("Running sysctl", timeout);
    validate_tty_contains("Starting network", timeout);
}

BOOST_AUTO_TEST_CASE(tty_initialized)
{
    validate_file_equals(path + "/started", "1", 10ms);
}

BOOST_AUTO_TEST_CASE(validate_before)
{
    validate_file_equals(path + "/validate_0_checksum_f1", "/mnt/nilfs2/f1: FAILED", timeout);
    validate_file_equals(path + "/validate_0_checksum_f2", "/mnt/nilfs2/f2: FAILED", timeout);
}

BOOST_AUTO_TEST_CASE(validate_after)
{
    validate_file_equals(path + "/validate_1_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_1_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(teardown)
{
    fixture.reset();
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_CASE(poweroff)
{
    validate_tty_contains("Requesting system reboot", timeout);
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(dedup)

constexpr auto suite_dir = "/dedup";
const string path = string(output_path) + suite_dir;

unique_ptr<Fixture> fixture;

BOOST_AUTO_TEST_CASE(setup, *utf::depends_on("generate/poweroff"))
{
    fixture = make_unique<Fixture>("commands/setup.sh", "commands/dedup.sh", "test_tty_output_dedup.log");
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_CASE(boot_ok, *utf::depends_on("generate/poweroff"))
{
    validate_tty_contains("Running sysctl", timeout);
    validate_tty_contains("Starting network", timeout);
}

BOOST_AUTO_TEST_CASE(tty_initialized, *utf::depends_on("generate/poweroff"))
{
    validate_file_equals(path + "/started", "1", 10ms);
}

BOOST_AUTO_TEST_CASE(validate_before, *utf::depends_on("generate/poweroff"))
{
    validate_file_equals(path + "/validate_0_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_0_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(validate_after, *utf::depends_on("generate/poweroff"))
{
    validate_file_equals(path + "/validate_1_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_1_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(validate_after_gc_cleanup, *utf::depends_on("generate/poweroff"))
{
    validate_file_equals(path + "/validate_2_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_2_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(teardown, *utf::depends_on("generate/poweroff"))
{
    fixture.reset();
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_CASE(poweroff, *utf::depends_on("generate/poweroff"))
{
    validate_tty_contains("Requesting system reboot", 500ms);
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(validate)

constexpr auto suite_dir = "/validate";
const string path = string(output_path) + suite_dir;

unique_ptr<Fixture> fixture;

BOOST_AUTO_TEST_CASE(setup, *utf::depends_on("dedup/poweroff"))
{
    fixture = make_unique<Fixture>("commands/setup.sh", "commands/validate.sh", "test_tty_output_validate.log");
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_CASE(boot_ok, *utf::depends_on("dedup/poweroff"))
{
    validate_tty_contains("Running sysctl", timeout);
    validate_tty_contains("Starting network", timeout);
}

BOOST_AUTO_TEST_CASE(tty_initialized, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/started", "1", 10ms);
}

BOOST_AUTO_TEST_CASE(before, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/validate_0_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_0_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(after_modification_of_second_file, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/validate_1_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_1_checksum_f2", "/mnt/nilfs2/f2: FAILED", timeout);
}

BOOST_AUTO_TEST_CASE(after_modification_of_second_file_after_remount, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/validate_2_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_2_checksum_f2", "/mnt/nilfs2/f2: FAILED", timeout);
}

BOOST_AUTO_TEST_CASE(after_restoring_second_file, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/validate_3_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_3_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(after_restoring_second_file_after_remount, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/validate_4_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_4_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(after_changing_first_file, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/validate_5_checksum_f1", "/mnt/nilfs2/f1: FAILED", timeout);
    validate_file_equals(path + "/validate_5_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(after_changing_first_file_after_remount, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/validate_6_checksum_f1", "/mnt/nilfs2/f1: FAILED", timeout);
    validate_file_equals(path + "/validate_6_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(after_restoring_first_file, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/validate_7_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_7_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(after_restoring_first_file_after_remount, *utf::depends_on("dedup/poweroff"))
{
    validate_file_equals(path + "/validate_8_checksum_f1", "/mnt/nilfs2/f1: OK", timeout);
    validate_file_equals(path + "/validate_8_checksum_f2", "/mnt/nilfs2/f2: OK", timeout);
}

BOOST_AUTO_TEST_CASE(teardown, *utf::depends_on("dedup/poweroff"))
{
    fixture.reset();
    BOOST_TEST(true);
}

BOOST_AUTO_TEST_CASE(poweroff, *utf::depends_on("dedup/poweroff"))
{
    validate_tty_contains("Requesting system reboot", timeout);
}

BOOST_AUTO_TEST_SUITE_END()