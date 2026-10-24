#!/usr/bin/env bash
# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
set -eo pipefail

PACKAGE_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ $(basename -- "$(dirname -- "$PACKAGE_ROOT")") != src ]]; then
  echo 'Place this repository inside your ROS workspace src directory first.' >&2
  exit 1
fi
WORKSPACE_ROOT=$(cd -- "$PACKAGE_ROOT/../.." && pwd)
if [[ ! -f /opt/ros/lyrical/setup.bash ]]; then
  echo 'Install ROS 2 Lyrical Desktop using the official Ubuntu installation guide first.' >&2
  exit 1
fi
source /etc/os-release
if [[ $ID != ubuntu || $VERSION_ID != 26.04 ]]; then
  echo 'This package is validated on Ubuntu 26.04 with ROS 2 Lyrical.' >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y ros-dev-tools python3-yaml
source /opt/ros/lyrical/setup.bash
if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  sudo rosdep init
fi
rosdep update --rosdistro lyrical
rosdep install --from-paths "$PACKAGE_ROOT" --ignore-src --rosdistro lyrical -y
python3 "$PACKAGE_ROOT/scripts/fetch_world.py"
cd "$WORKSPACE_ROOT"
colcon build --symlink-install --packages-select tiago_jetty \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
echo
echo 'Build complete. In your terminal:'
echo "source $WORKSPACE_ROOT/install/setup.bash"
echo 'ros2 launch tiago_jetty bringup.launch.py'
