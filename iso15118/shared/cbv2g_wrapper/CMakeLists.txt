cmake_minimum_required(VERSION 3.14)
project(cbv2g_json_wrapper VERSION 1.0.0 LANGUAGES C)

# Set C standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Build as shared library
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Try to find libcbv2g via CMake package first (Yocto build)
find_package(cbv2g QUIET)

if(cbv2g_FOUND)
    message(STATUS "Found libcbv2g via find_package")
    set(USE_SYSTEM_LIBCBV2G ON)
else()
    message(STATUS "libcbv2g package not found, looking for source directory")
    set(USE_SYSTEM_LIBCBV2G OFF)

    # Find libcbv2g source directory
    set(LIBCBV2G_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../libcbv2g"
        CACHE PATH "Path to libcbv2g source directory")

    if(NOT EXISTS "${LIBCBV2G_ROOT}/include/cbv2g")
        message(FATAL_ERROR "libcbv2g not found. Either install the cbv2g package "
                            "or set LIBCBV2G_ROOT to the source directory.")
    endif()
endif()

# cJSON library (embedded)
add_library(cjson STATIC
    third_party/cJSON/cJSON.c
)
target_include_directories(cjson PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/cJSON
)

# Wrapper sources — only AppHandshake converter for now.
# DIN, ISO-2, and ISO-20 converters will be added in subsequent PRs.
set(WRAPPER_SOURCES
    src/cbv2g_json_wrapper.c
    src/json_utils.c
    src/apphand_converter.c
)

if(USE_SYSTEM_LIBCBV2G)
    # Using system-installed libcbv2g
    add_library(cbv2g_json_wrapper SHARED ${WRAPPER_SOURCES})

    target_include_directories(cbv2g_json_wrapper
        PUBLIC
            ${CMAKE_CURRENT_SOURCE_DIR}/include
        PRIVATE
            ${CMAKE_CURRENT_SOURCE_DIR}/src
            ${CMAKE_CURRENT_SOURCE_DIR}/third_party/cJSON
    )

    target_link_libraries(cbv2g_json_wrapper
        PRIVATE
            cjson
            cbv2g::cbv2g
    )
else()
    # Build libcbv2g sources directly into our library
    set(CBVG_COMMON_SOURCES
        ${LIBCBV2G_ROOT}/lib/cbv2g/common/exi_basetypes_decoder.c
        ${LIBCBV2G_ROOT}/lib/cbv2g/common/exi_basetypes_encoder.c
        ${LIBCBV2G_ROOT}/lib/cbv2g/common/exi_basetypes.c
        ${LIBCBV2G_ROOT}/lib/cbv2g/common/exi_bitstream.c
        ${LIBCBV2G_ROOT}/lib/cbv2g/common/exi_header.c
        ${LIBCBV2G_ROOT}/lib/cbv2g/common/exi_types_decoder.c
    )

    set(CBVG_APPHAND_SOURCES
        ${LIBCBV2G_ROOT}/lib/cbv2g/app_handshake/appHand_Datatypes.c
        ${LIBCBV2G_ROOT}/lib/cbv2g/app_handshake/appHand_Decoder.c
        ${LIBCBV2G_ROOT}/lib/cbv2g/app_handshake/appHand_Encoder.c
    )

    set(CBVG_TP_SOURCES
        ${LIBCBV2G_ROOT}/lib/cbv2g/exi_v2gtp.c
    )

    add_library(cbv2g_json_wrapper SHARED
        ${CBVG_COMMON_SOURCES}
        ${CBVG_APPHAND_SOURCES}
        ${CBVG_TP_SOURCES}
        ${WRAPPER_SOURCES}
    )

    target_include_directories(cbv2g_json_wrapper
        PUBLIC
            ${CMAKE_CURRENT_SOURCE_DIR}/include
        PRIVATE
            ${CMAKE_CURRENT_SOURCE_DIR}/src
            ${CMAKE_CURRENT_SOURCE_DIR}/third_party/cJSON
            ${LIBCBV2G_ROOT}/include
    )

    target_link_libraries(cbv2g_json_wrapper
        PRIVATE
            cjson
    )
endif()

# Set library version
set_target_properties(cbv2g_json_wrapper PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
)

# Install rules
install(TARGETS cbv2g_json_wrapper
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(FILES include/cbv2g_json_wrapper.h
    DESTINATION include
)

# Optional: Build test executable
option(BUILD_TESTS "Build test executable" OFF)
if(BUILD_TESTS)
    add_executable(cbv2g_wrapper_test
        tests/test_main.c
    )
    target_link_libraries(cbv2g_wrapper_test
        cbv2g_json_wrapper
    )
endif()
