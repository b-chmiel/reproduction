cmake_minimum_required(VERSION 3.10)
project(tty_runner)

set(CMAKE_CXX_STANDARD 20)

include(CheckLibraryExists)
CHECK_LIBRARY_EXISTS(explain explain_errno_ioctl "/usr/include" HAVE_LIBEXPLAIN)

if (${HAVE_LIBEXPLAIN})
	add_definitions(-DHAVE_LIBEXPLAIN)
endif()

find_package(Boost 1.81 COMPONENTS program_options REQUIRED)

add_subdirectory(src)