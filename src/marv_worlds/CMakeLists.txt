cmake_minimum_required(VERSION 3.10.2)
project(marv_worlds)

find_package(ament_cmake REQUIRED)

ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/hooks/resource_paths.dsv.in"
  "${CMAKE_CURRENT_SOURCE_DIR}/hooks/resource_paths.sh"
)

# Generate marv_auv from bluerov2_heavy when available.
if(EXISTS "$ENV{HOME}/bluerov2_gz/models/bluerov2_heavy/model.sdf")
  execute_process(
    COMMAND python3 "${CMAKE_CURRENT_SOURCE_DIR}/scripts/build_marv_auv_model.py"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
  )
endif()

install(DIRECTORY
  models
  worlds
  launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/gz_pose_bridge.py
  scripts/gz_image_bridge.py
  scripts/gz_clock_bridge.py
  scripts/build_marv_auv_model.py
  scripts/gz_spawn_with_retry.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
