include(CTest)
include(Catch)

add_executable(tests test.cpp)
target_link_libraries(tests tty_runner Catch2::Catch2WithMain)
target_include_directories(tests PRIVATE ${CMAKE_SOURCE_DIR}/src)