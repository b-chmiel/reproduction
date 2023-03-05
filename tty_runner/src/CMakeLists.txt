file(GLOB TTY_SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/*.cpp )
add_executable(tty ${TTY_SOURCES})

target_include_directories(tty PRIVATE ${Boost_INCLUDE_DIR})
target_link_libraries(tty explain ${Boost_LIBRARIES})