# Install script for directory: /home/michael/project/rv1126/RK_SDK_rv1126_rv1109_linux_v1.3.0_20200921/rv1126_rv1109/external/rknpu/rknn/rknn_api/examples/rknn_mobilenet_demo

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/michael/project/rv1126/RK_SDK_rv1126_rv1109_linux_v1.3.0_20200921/rv1126_rv1109/external/rknpu/rknn/rknn_api/examples/rknn_mobilenet_demo/install/tcore_rv")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/./tcore_rv" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/./tcore_rv")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/./tcore_rv"
         RPATH "lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/." TYPE EXECUTABLE FILES "/home/michael/project/rv1126/RK_SDK_rv1126_rv1109_linux_v1.3.0_20200921/rv1126_rv1109/external/rknpu/rknn/rknn_api/examples/rknn_mobilenet_demo/build/tcore_rv")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/./tcore_rv" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/./tcore_rv")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/./tcore_rv"
         OLD_RPATH "/home/michael/project/rv1126/RK_SDK_rv1126_rv1109_linux_v1.3.0_20200921/rv1126_rv1109/external/rknpu/rknn/rknn_api/examples/rknn_mobilenet_demo/../../librknn_api/lib:"
         NEW_RPATH "lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/./tcore_rv")
    endif()
  endif()
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/./" TYPE DIRECTORY FILES "/home/michael/project/rv1126/RK_SDK_rv1126_rv1109_linux_v1.3.0_20200921/rv1126_rv1109/external/rknpu/rknn/rknn_api/examples/rknn_mobilenet_demo/model")
endif()

if(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE PROGRAM FILES "/home/michael/project/rv1126/RK_SDK_rv1126_rv1109_linux_v1.3.0_20200921/rv1126_rv1109/external/rknpu/rknn/rknn_api/examples/rknn_mobilenet_demo/../../librknn_api/lib/librknn_api.so")
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/michael/project/rv1126/RK_SDK_rv1126_rv1109_linux_v1.3.0_20200921/rv1126_rv1109/external/rknpu/rknn/rknn_api/examples/rknn_mobilenet_demo/build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
