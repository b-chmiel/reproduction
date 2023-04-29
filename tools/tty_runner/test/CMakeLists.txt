add_executable(tests test.cpp)
target_link_libraries(tests tty_runner ${Boost_UNIT_TEST_FRAMEWORK_LIBRARY})
target_include_directories(tests PRIVATE ${CMAKE_SOURCE_DIR}/src)