/****************************************************************************
 *
 * Copyright 2020 PX4 Development Team. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 * may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 ****************************************************************************/

/**
 * @brief Offboard control example with takeoff to 5 m, then circle
 * @file offboard_control_circle.cpp
 * @addtogroup examples
 */

#include <cmath> // for std::sin, std::cos
#include <px4_msgs/msg/offboard_control_mode.hpp>
#include <px4_msgs/msg/trajectory_setpoint.hpp>
#include <px4_msgs/msg/vehicle_command.hpp>
#include <px4_msgs/msg/vehicle_control_mode.hpp>
#include <rclcpp/rclcpp.hpp>
#include <stdint.h>

#include <chrono>
#include <iostream>

using namespace std::chrono;
using namespace std::chrono_literals;
using namespace px4_msgs::msg;

class OffboardControl : public rclcpp::Node {
public:
  OffboardControl()
      : Node("offboard_control_circle"), radius_(5.0), circle_duration_s_(20.0),
        offboard_setpoint_counter_(0) {
    offboard_control_mode_publisher_ =
        this->create_publisher<OffboardControlMode>(
            "/fmu/in/offboard_control_mode", 10);
    trajectory_setpoint_publisher_ = this->create_publisher<TrajectorySetpoint>(
        "/fmu/in/trajectory_setpoint", 10);
    vehicle_command_publisher_ =
        this->create_publisher<VehicleCommand>("/fmu/in/vehicle_command", 10);

    // Compute angular speed so that one full circle (2π radians) takes
    // circle_duration_s_ seconds. Since our timer fires every 100 ms, we will
    // increment angle by delta_theta each publish.
    omega_ = 2.0 * M_PI / circle_duration_s_;

    auto timer_callback = [this]() -> void {
      // After 10 setpoints, switch to OFFBOARD and arm
      if (offboard_setpoint_counter_ == 10) {
        // Switch to OFFBOARD mode (custom_mode 6, base_mode 1 = PX4_OFFBOARD)
        this->publish_vehicle_command(VehicleCommand::VEHICLE_CMD_DO_SET_MODE,
                                      1.0f, 6.0f);

        // Arm the vehicle
        this->arm();
      }

      // Always publish mode + setpoint together
      publish_offboard_control_mode();
      publish_trajectory_setpoint();

      // Stop incrementing after a large number so that the circle keeps going
      offboard_setpoint_counter_++;
    };

    // Fire the callback at 10 Hz (every 100 ms)
    timer_ = this->create_wall_timer(100ms, timer_callback);
  }

  void arm();
  void disarm();

private:
  rclcpp::TimerBase::SharedPtr timer_;

  rclcpp::Publisher<OffboardControlMode>::SharedPtr
      offboard_control_mode_publisher_;
  rclcpp::Publisher<TrajectorySetpoint>::SharedPtr
      trajectory_setpoint_publisher_;
  rclcpp::Publisher<VehicleCommand>::SharedPtr vehicle_command_publisher_;

  // Circle parameters
  const double radius_;            // meters
  const double circle_duration_s_; // seconds for one full revolution
  double omega_;                   // rad/s

  // Count how many setpoints have been sent
  std::atomic<uint64_t> offboard_setpoint_counter_;

  void publish_offboard_control_mode();
  void publish_trajectory_setpoint();
  void publish_vehicle_command(uint16_t command, float param1 = 0.0f,
                               float param2 = 0.0f);
};

/**
 * @brief Send a command to Arm the vehicle
 */
void OffboardControl::arm() {
  publish_vehicle_command(VehicleCommand::VEHICLE_CMD_COMPONENT_ARM_DISARM,
                          1.0f);
  RCLCPP_INFO(this->get_logger(), "Arm command sent");
}

/**
 * @brief Send a command to Disarm the vehicle
 */
void OffboardControl::disarm() {
  publish_vehicle_command(VehicleCommand::VEHICLE_CMD_COMPONENT_ARM_DISARM,
                          0.0f);
  RCLCPP_INFO(this->get_logger(), "Disarm command sent");
}

/**
 * @brief Publish the offboard control mode.
 *        For this example, only position control is active.
 */
void OffboardControl::publish_offboard_control_mode() {
  OffboardControlMode msg{};
  msg.position = true;
  msg.velocity = false;
  msg.acceleration = false;
  msg.attitude = false;
  msg.body_rate = false;
  msg.timestamp = this->get_clock()->now().nanoseconds() / 1000;
  offboard_control_mode_publisher_->publish(msg);
}

/**
 * @brief Publish a trajectory setpoint
 *        First climb and hold at 5 m (0,0,−5) for 5 seconds, then fly a circle
 * of radius 5 m at z=−5.
 */
void OffboardControl::publish_trajectory_setpoint() {
  TrajectorySetpoint msg{};
  msg.timestamp = this->get_clock()->now().nanoseconds() / 1000;

  // How many cycles have passed at 10 Hz? (i.e., each loop is 0.1 s)
  // Use that to determine when to switch from 'hover at (0,0, −5)' to 'circle'
  const uint64_t hover_cycles = 50; // 50 × 0.1 s = 5 seconds

  if (offboard_setpoint_counter_ < hover_cycles) {
    // Still in takeoff‐hover phase: hold x=0, y=0, z=−5
    msg.position = {0.0f, 0.0f, -5.0f};
    msg.yaw = 0.0f; // face along +x axis
  } else {
    // Enter circle‐flying phase
    double t = (offboard_setpoint_counter_ - hover_cycles) *
               0.1;            // time elapsed since starting circle
    double angle = omega_ * t; // radians

    float x = static_cast<float>(radius_ * std::cos(angle));
    float y = static_cast<float>(radius_ * std::sin(angle));
    float z = -5.0f; // maintain 5 m altitude

    msg.position = {x, y, z};

    // Yaw so that the drone always faces forward along its circular path:
    // yaw = angle + π/2  (so that velocity vector is tangent)
    msg.yaw = static_cast<float>(angle + M_PI / 2.0);
  }

  trajectory_setpoint_publisher_->publish(msg);
}

/**
 * @brief Publish vehicle commands
 * @param command   Command code (matches VehicleCommand and MAVLink MAV_CMD
 * codes)
 * @param param1    Command parameter 1
 * @param param2    Command parameter 2
 */
void OffboardControl::publish_vehicle_command(uint16_t command, float param1,
                                              float param2) {
  VehicleCommand msg{};
  msg.param1 = param1;
  msg.param2 = param2;
  msg.command = command;
  msg.target_system = 1;
  msg.target_component = 1;
  msg.source_system = 1;
  msg.source_component = 1;
  msg.from_external = true;
  msg.timestamp = this->get_clock()->now().nanoseconds() / 1000;
  vehicle_command_publisher_->publish(msg);
}

int main(int argc, char *argv[]) {
  std::cout << "Starting offboard control (takeoff + circle) node..."
            << std::endl;
  setvbuf(stdout, NULL, _IONBF, BUFSIZ);
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<OffboardControl>());

  rclcpp::shutdown();
  return 0;
}
