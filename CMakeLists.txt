cmake_minimum_required(VERSION 3.22)
project(tiago_jetty)

find_package(ament_cmake REQUIRED)

if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/assets/jetty_models/Distribution_Warehouse/model.sdf")
  message(FATAL_ERROR "Jetty world assets are missing. Run: python3 scripts/fetch_world.py")
endif()

install(DIRECTORY launch config urdf meshes worlds
  DESTINATION share/${PROJECT_NAME})
install(DIRECTORY assets/jetty_models/
  DESTINATION share/${PROJECT_NAME}/models)
install(FILES SOURCES.json THIRD_PARTY.md LICENSE
  DESTINATION share/${PROJECT_NAME})
install(DIRECTORY LICENSES DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/verify_sim.py DESTINATION lib/${PROJECT_NAME})

ament_package()
