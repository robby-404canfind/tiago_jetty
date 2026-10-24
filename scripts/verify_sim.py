#!/usr/bin/env python3
# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
"""Verify live data; --drive and --actions also exercise the simulated robot."""
import argparse
import json
import math
from pathlib import Path
import time

from action_msgs.msg import GoalStatus
from control_msgs.action import FollowJointTrajectory
from controller_manager_msgs.srv import ListControllers
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from play_motion2_msgs.action import PlayMotion2
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, Imu, JointState, LaserScan
import tf2_ros
from trajectory_msgs.msg import JointTrajectoryPoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--drive', action='store_true')
    parser.add_argument('--actions', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    rclpy.init()
    node = Node('tiago_jetty_verification', parameter_overrides=[Parameter('use_sim_time', value=True)])
    latest, counts = {}, {}

    def receive(name, message):
        latest[name] = message
        counts[name] = counts.get(name, 0) + 1

    subscriptions = [node.create_subscription(
        kind, topic, lambda message, name=name: receive(name, message), qos_profile_sensor_data)
        for kind, topic, name in [
            (LaserScan, '/scan_raw', 'laser'),
            (Odometry, '/mobile_base_controller/odom', 'odom'),
            (JointState, '/joint_states', 'joints'),
            (Image, '/head_front_camera/rgb/image_raw', 'rgb'),
            (Image, '/head_front_camera/depth/image_raw', 'depth'),
            (Imu, '/base_imu', 'imu'),
        ]]
    buffer = tf2_ros.Buffer()
    listener = tf2_ros.TransformListener(buffer, node)
    publisher = node.create_publisher(Twist, '/cmd_vel', 10)

    def spin_for(seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.025)

    def wait_future(future, timeout=90):
        rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
        if not future.done():
            raise TimeoutError('A simulation service or action did not finish in time.')
        return future.result()

    def position():
        pose = latest['odom'].pose.pose
        return [pose.position.x, pose.position.y,
                2 * math.atan2(pose.orientation.z, pose.orientation.w)]

    def drive(x, z, seconds):
        message = Twist()
        message.linear.x, message.angular.z = x, z
        start = node.get_clock().now().nanoseconds
        deadline = time.monotonic() + 45
        while (node.get_clock().now().nanoseconds - start) / 1e9 < seconds:
            if time.monotonic() > deadline:
                raise TimeoutError('Simulation time stopped during the velocity test.')
            publisher.publish(message)
            spin_for(0.05)
        publisher.publish(Twist())
        spin_for(1)

    def action(action_type, topic, goal):
        client = ActionClient(node, action_type, topic)
        try:
            if not client.wait_for_server(timeout_sec=30):
                raise TimeoutError(f'Action server unavailable: {topic}')
            handle = wait_future(client.send_goal_async(goal))
            if not handle.accepted:
                raise RuntimeError(f'Action rejected: {topic}')
            result = wait_future(handle.get_result_async(), timeout=150)
            entry = {'status': result.status,
                     'succeeded': result.status == GoalStatus.STATUS_SUCCEEDED}
            if action_type == PlayMotion2:
                entry.update(success=result.result.success, error=result.result.error)
            else:
                entry.update(error_code=result.result.error_code, error=result.result.error_string)
            spin_for(0.5)
            entry['joint_positions'] = dict(zip(latest['joints'].name, latest['joints'].position))
            print(json.dumps({topic: entry}), flush=True)
            return entry
        finally:
            client.destroy()

    report = {'passed': False}
    try:
        required = {'laser', 'odom', 'joints', 'rgb', 'depth', 'imu'}
        deadline = time.monotonic() + 90
        while required - latest.keys() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        report['missing_topics'] = sorted(required - latest.keys())
        if report['missing_topics']:
            raise RuntimeError(f"Missing data: {report['missing_topics']}")
        wall_start = time.monotonic()
        sim_start = node.get_clock().now().nanoseconds
        spin_for(5)
        report['real_time_factor_observed'] = ((node.get_clock().now().nanoseconds - sim_start) / 1e9 /
                                              (time.monotonic() - wall_start))
        report['message_counts'] = dict(counts)
        scan = latest['laser']
        finite = [value for value in scan.ranges if math.isfinite(value)]
        front = [value for index, value in enumerate(scan.ranges)
                 if abs(scan.angle_min + index * scan.angle_increment) < 0.3 and math.isfinite(value)]
        report['laser'] = {'frame': scan.header.frame_id, 'samples': len(scan.ranges),
                           'finite_samples': len(finite), 'front_min_m': min(front, default=None)}
        for name in ['rgb', 'depth']:
            message = latest[name]
            report[name] = {'width': message.width, 'height': message.height,
                            'encoding': message.encoding, 'bytes': len(message.data)}
        report['tf'] = {}
        for child in ['base_footprint', 'base_laser_link', 'head_front_camera_optical_frame']:
            try:
                buffer.lookup_transform('odom', child, rclpy.time.Time())
                report['tf'][child] = True
            except tf2_ros.TransformException:
                report['tf'][child] = False
        controller_client = node.create_client(ListControllers, '/controller_manager/list_controllers')
        if not controller_client.wait_for_service(timeout_sec=20):
            raise TimeoutError('Controller manager unavailable.')
        controllers = wait_future(controller_client.call_async(ListControllers.Request()), timeout=30)
        report['controllers'] = {controller.name: controller.state for controller in controllers.controller}
        node.destroy_client(controller_client)
        if args.drive:
            if report['laser']['front_min_m'] is None or report['laser']['front_min_m'] < 1.0:
                raise RuntimeError('The forward test needs at least one metre of clear space.')
            before = position()
            drive(0.15, 0.0, 3)
            middle = position()
            drive(0.0, 0.2, 2)
            after = position()
            report['drive'] = {'before': before, 'after_forward': middle, 'after_turn': after,
                               'distance_m': math.dist(before[:2], middle[:2]),
                               'yaw_change_rad': math.atan2(math.sin(after[2] - middle[2]),
                                                            math.cos(after[2] - middle[2]))}
        if args.actions:
            report['actions'] = {}
            for controller, joints, positions, seconds in [
                ('torso', ['torso_lift_joint'], [0.35], 3),
                ('head', ['head_1_joint', 'head_2_joint'], [0.0, -0.5], 3),
                ('gripper', ['gripper_left_finger_joint', 'gripper_right_finger_joint'], [0.04, 0.04], 2),
            ]:
                goal = FollowJointTrajectory.Goal()
                goal.trajectory.joint_names = joints
                point = JointTrajectoryPoint()
                point.positions = positions
                point.time_from_start.sec = seconds
                goal.trajectory.points = [point]
                report['actions'][controller] = action(
                    FollowJointTrajectory, f'/{controller}_controller/follow_joint_trajectory', goal)
            wave = PlayMotion2.Goal()
            wave.motion_name = 'wave'
            report['actions']['wave'] = action(PlayMotion2, '/play_motion2', wave)
        expected = {'joint_state_broadcaster', 'mobile_base_controller', 'arm_controller',
                    'torso_controller', 'head_controller', 'gripper_controller', 'ft_sensor_controller'}
        report['passed'] = (all(report['tf'].values()) and len(finite) > 100 and
                            all(report['controllers'].get(name) == 'active' for name in expected))
        if args.drive:
            report['passed'] &= report['drive']['distance_m'] > 0.1 and abs(report['drive']['yaw_change_rad']) > 0.1
        if args.actions:
            report['passed'] &= all(entry['succeeded'] for entry in report['actions'].values())
            report['passed'] &= report['actions']['wave']['success']
    except Exception as error:
        report['error'] = str(error)
    finally:
        publisher.publish(Twist())
        text = json.dumps(report, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + '\n')
        print(text, flush=True)
        node.destroy_node()
        rclpy.shutdown()
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
