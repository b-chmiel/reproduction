.PHONY = compile test

BUILD_DIR = build

BUILD_SYSTEM_FILENAME=build.ninja
BUILD_SYSTEM_NAME=Ninja
BUILD_SYSTEM_COMMAND=ninja

compile: $(BUILD_DIR)/$(BUILD_SYSTEM_FILENAME) 
	cmake --build ${BUILD_DIR}

$(BUILD_DIR)/$(BUILD_SYSTEM_FILENAME): CMakeLists.txt src/CMakeLists.txt test/CMakeLists.txt
	CXX=clang++ cmake . \
		-DCMAKE_BUILD_TYPE=Debug \
		-DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
		-G"$(BUILD_SYSTEM_NAME)" \
		-B $(BUILD_DIR)

test: FORCE
	./${BUILD_DIR}/test/tests \
		--log_level=all

clean:
	- rm -rf $(BUILD_DIR)

FORCE:
