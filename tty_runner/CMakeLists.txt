cmake_minimum_required(VERSION 3.10)
project(tty_runner)

set(CMAKE_CXX_STANDARD 20)

include(CheckLibraryExists)
CHECK_LIBRARY_EXISTS(explain explain_errno_ioctl "/usr/include" HAVE_LIBEXPLAIN)

add_executable(tty tty.cpp)
target_link_libraries(tty explain)