#include "tty_runner.hpp"
#include <boost/test/included/unit_test.hpp>
#include <chrono>
#include <string>
#include <thread>

namespace test
{
using namespace std::this_thread;
using namespace std::chrono_literals;

inline void tty_contains_with_timeout(const std::string& query, const std::chrono::milliseconds timeout)
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

inline long long tty_get_filesystem_size(int validation_id)
{
    // 'BEGIN_SIZE .* SIZE \d \d+ END_SIZE'
    const auto size_measurements = tty::output_matches("BEGIN_SIZE");
    std::cout << "MEASUREMENTS:" << std::endl;
    for (auto m : size_measurements)
    {
        std::cout << m << std::endl;
    }

    return 0;
}

}