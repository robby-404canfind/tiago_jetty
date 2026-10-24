# 실행 검증

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
