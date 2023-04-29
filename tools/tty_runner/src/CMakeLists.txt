add_library(tty_runner 
	arg.cpp
	tty_executor.cpp
	pty_launcher.cpp
	tty_runner.cpp
)

target_include_directories(tty_runner PRIVATE ${BOOST_INCLUDE_DIR} ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(tty_runner explain ${Boost_LIBRARIES})

add_executable(tty main.cpp)
target_link_libraries(tty PRIVATE tty_runner)