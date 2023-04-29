cmake_minimum_required(VERSION 3.10)
project(tty_runner)

set(CMAKE_CXX_STANDARD 23)

include(CheckLibraryExists)
CHECK_LIBRARY_EXISTS(explain explain_errno_ioctl "/usr/include" HAVE_LIBEXPLAIN)

if (${HAVE_LIBEXPLAIN})
	add_definitions(-DHAVE_LIBEXPLAIN)
endif()

find_package(Boost 1.81 COMPONENTS program_options REQUIRED)

Include(FetchContent)

FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG        v3.0.1 # or a later release
)

FetchContent_MakeAvailable(Catch2)
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)

add_subdirectory(src)
add_subdirectory(test)