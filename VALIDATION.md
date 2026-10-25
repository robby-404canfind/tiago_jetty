# 0.1.1 실행 검증

2026-10-25, Ubuntu 26.04.1 / ROS 2 Lyrical / Gazebo Jetty 10.5.0에서 확인했습니다. Gazebo 화면은 원격 데스크톱으로 직접 확인했습니다.

원운동 명령에서 양쪽 바퀴의 속도 차이가 유지되지 않던 문제를 수정했습니다. 같은 시작 위치에서 비교한 뒤 바퀴 관절의 수동 감쇠와 마찰을 줄였으며, 바퀴와 바닥 사이의 접촉 마찰은 유지했습니다. 회전 명령에 대한 기본 보정값은 `wheel_separation_multiplier: 1.1`입니다. 오도메트리와 실제 위치의 완전한 일치를 검증 조건으로 두지는 않았습니다.

기본 생성 위치를 장애물과 떨어진 통로 `(8, -4)`로 옮겼습니다. 몸통의 전체 높이 이동에는 최대 속도 0.07 m/s를 고려해 검증 명령의 시간을 6초로 늘렸습니다.

`ros2 run tiago_jetty verify_sim.py --drive --actions`와 서비스·액션 실습을 확인한 결과입니다. 측정값은 [validation-lyrical-jetty-0.1.1.json](test/validation-lyrical-jetty-0.1.1.json)에 있습니다.

| 항목 | 결과 |
|---|---|
| 전진 / 제자리 회전 | 약 0.451 m / 0.406 rad |
| 제어기 / 센서 / TF | 제어기 7개 active, 레이저·RGB·깊이·IMU·관절·오도메트리 수신, TF 연결 확인 |
| 원운동 서비스 | 모델 실제 경로 약 6.09 m, 누적 회전 약 6.84 rad |
| 서비스 시작 / 정지 | SetBool 요청에 따라 주행 / 정지 확인 |
| 커스텀 서비스 | 전진·후진·제자리 회전·곡선 주행 4개 요청 성공 |
| 관절 액션 | 그리퍼 열기·닫기, 고개 숙이기·들기, 몸통 올리기·내리기 성공 |
| 사전 정의 모션 | home, head_tour, wave, reach_floor, reach_max 모두 성공 |
| 회전 액션 실습 | 절대 목표 방향, 시뮬레이션 시간, 회전량 결과, 커스텀 success 응답 확인 |

Gazebo만 표시한 이번 실행의 5초 측정 구간에서 실시간 비율은 약 0.66이었습니다. 아래 0.1.0의 RViz 동시 실행 수치와는 화면 구성이 다릅니다. 월드 전체의 시각 모델은 유지했습니다.

MoveIt의 3D 점유 지도 갱신, 창고 물체에 대한 3D 충돌 회피, SLAM/Nav2 전체 자율주행은 이번 검증 범위에 포함하지 않습니다.

---

# 0.1.0 검증 기록

2026-10-24, Ubuntu 26.04.1 / ROS 2 Lyrical / Gazebo Jetty 10.5.0에서 확인했습니다. 시뮬레이터와 RViz 화면은 원격 데스크톱으로 직접 확인했습니다.

## 설치와 시작

- 공식 소스의 특정 버전에서 Jetty 월드 모델을 새로 다운로드했습니다.
- `scripts/setup.bash`로 의존성을 설치하고 `~/ros2_ws/src/tiago_jetty`에서 패키지를 빌드했습니다.
- PAL 소스 워크스페이스를 사용하지 않고, 기본 Fast DDS와 배포된 Lyrical 패키지로 실행했습니다.
- 모델의 메시 경로 34개와 SRDF 링크를 확인했습니다.
- 새 실행에서 제어기 7개가 한 번의 요청으로 모두 활성화되고 spawner가 정상 종료되는 것을 확인했습니다. 초기 그래픽 로딩을 기다릴 수 있도록 서비스 응답 제한 시간을 120초로 설정했습니다.

## 동작

`ros2 run tiago_jetty verify_sim.py --drive --actions`로 확인한 결과입니다. 원본 측정값은 [validation-lyrical-jetty.json](test/validation-lyrical-jetty.json)에 있습니다.

| 항목 | 결과 |
|---|---|
| 짧은 전진 | 주행 거리 약 0.438 m |
| 회전 | 약 0.402 rad |
| 제어기 | 주행·관절 상태·팔·몸통·머리·그리퍼·FT 센서 모두 active |
| 레이저 | `/scan_raw`, 666개 거리 샘플 수신 |
| RGB / 깊이 | 640×480, `rgb8` / `32FC1` 수신 |
| IMU / 관절 / 주행 거리 | 메시지 수신 |
| TF | odom → base_footprint / base_laser_link / camera optical frame 연결 |
| 몸통 | 0.35 m 목표, SUCCEEDED |
| 머리 | `[0.0, -0.5]` 목표, SUCCEEDED |
| 그리퍼 | 양쪽 0.04 m 목표, SUCCEEDED |
| 손 흔들기 | 계획을 포함한 `wave`, success=true / SUCCEEDED |
| RViz | 로봇·레이저 표시, Global Status OK |

## 성능과 범위

Intel i9-14900HX / RTX 4080 Laptop GPU 12 GB / RAM 32 GB에서 창고 전체와 RViz를 함께 실행했을 때, 5초 구간의 실시간 비율은 약 0.46이었습니다. 월드가 크기 때문에 PC 성능과 화면 구성에 따라 차이가 있습니다. 이 노트북은 기본 실행 시 내장 그래픽을 사용했으며, `nvidia:=true`를 적용한 뒤 실제 NVIDIA 렌더러 사용을 확인했습니다.

관절 제한은 유지했습니다. 끝 위치 근처에서 제한 관련 진단 메시지가 나올 수 있으며, 위 액션의 실제 관절 상태와 성공 결과를 함께 확인했습니다.

현재 MoveIt의 3D 점유 지도 갱신기는 설정하지 않았습니다. 팔 동작 계획은 확인했지만 창고 물체에 대한 3D 충돌 회피와 SLAM/Nav2 전체 자율주행은 후속 검증이 필요합니다.
