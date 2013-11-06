cmake_minimum_required(VERSION 2.8)
project(nanomsg-virtual-test C)

include(ExternalProject)
ExternalProject_Add(
  libnanomsg
  SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/projects/nanomsg
  CONFIGURE_COMMAND sh autogen.sh &&
    ${CMAKE_CURRENT_SOURCE_DIR}/projects/nanomsg/configure
    --prefix=${CMAKE_CURRENT_BINARY_DIR}/projects/nanomsg/dist/
  PREFIX ${CMAKE_CURRENT_BINARY_DIR}/projects/nanomsg
  BUILD_COMMAND make
  BUILD_IN_SOURCE 1
)
include_directories(SYSTEM
    ${CMAKE_CURRENT_BINARY_DIR}/projects/nanomsg/dist/include)
link_directories(
    ${CMAKE_CURRENT_BINARY_DIR}/projects/nanomsg/dist/lib)

install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/projects/nanomsg/dist/
    DESTINATION "${CMAKE_INSTALL_PREFIX}")

add_subdirectory(projects/nanoconfig)
add_subdirectory(projects/topologist)
