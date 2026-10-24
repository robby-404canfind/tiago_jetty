# Third-party sources

TIAGo is a PAL Robotics robot. This educational integration is not an official PAL Robotics distribution.

The robot model, used meshes, semantic model, controller settings and predefined motions are derived from PAL Robotics' Apache-2.0 sources. `SOURCES.json` records exact revisions of `tiago_robot`, `pmb2_robot`, `pal_gripper`, `pal_urdf_utils`, `tiago_moveit_config`, and `tiago_simulation`. Their license texts are preserved in `LICENSES/`.

Changes include consolidating the fixed PMB2 / TIAGo arm / PAL gripper configuration into this package, rewriting resource paths, initializing joints in the folded pose, mapping semantic camera links to the current color-frame names, adapting MoveIt planning configuration, and supplying finite acceleration limits for simulation. These settings are not physical robot specifications.

The warehouse world is derived from [gazebosim/jetty_demo](https://github.com/gazebosim/jetty_demo), Apache-2.0, at the revision in `SOURCES.json`. The world adds an IMU system and uses a 5 ms physics step for the 100 Hz controller. The original warehouse layout and visual models are retained. The model assets are fetched from that official repository by `scripts/fetch_world.py`; model-specific author metadata remains in the upstream `model.config` files. Their upstream license is preserved in `LICENSES/jetty_demo-LICENSE`.

`play_motion2`, Gazebo, `ros_gz`, `gz_ros2_control`, MoveIt, ROS controllers and `twist_stamper` are installed as dependencies from the ROS repository and retain their respective licenses.
