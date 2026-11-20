# 招聘展示视频

本目录仅收录两段已完成的成片，便于查看限定场景演示；原片及同期 bag、日志仍保存在仓库外本机证据目录。成片有明确标识的说明画面，不把文字卡当作原始录屏。V0.3 的恢复对照使用[离线图表](../docs/V0.3_D7_EVIDENCE_PRESENTATION.md)，没有新增现场录像。

| 文件 | 展示内容 | 时长 | SHA-256 |
| --- | --- | --- | --- |
| [V0.1 两站配送](B7_two_stop_delivery_demo_final_2026-10-21.webm) | 取货、送达顺序与客户端结果；不展示 V0.2 临时障碍 | 63.210 秒 | `ffe7877cdb283be52035b564e98aba77412c9df70a137a23c375ee18ee0e5202` |
| [V0.2 临时障碍配送](C8_temporary_obstacle_two_stop_demo_final.webm) | 箱体出现、RViz 扫描/代价/路径、机器人运动及两站成功 | 110.200 秒 | `20f519a267cd36bd47aee0d7e57e213e790cb0ad9aed917f59e222a02b49c516` |

对应原片的本机索引为 `~/mobile_robot_delivery_acceptance_logs/B7_2026-10-21/B7_two_stop_delivery_demo_2026-10-21.webm`（SHA-256 `70bd0437634b5a23d7975e592c747d7bfb42634fcd31ef785c8aa85d3aaa99da`）及 `~/mobile_robot_delivery_acceptance_logs/C8_2026-10-28/run_001/raw_capture.webm`（SHA-256 `013239f6a8509d15d949221b0515b747322b93f5782db43484436e9f3c5c37cf`）。这些路径不是可从 GitHub 下载的原片链接。C8 画面与同期 bag 的既有核对见[项目状态 C8 记录](../docs/PROJECT_STATUS.md)；本次入库只复核成片文件、哈希、媒体时长和抽样画面，没有重新做逐帧或仿真验收。

两段视频都只展示各自一次限定场景的结果。`/delivery_task` 返回成功不表示底盘瞬时静止；旧 odom 偏航及 C6 删除后全局 costmap 高代价残留仍未解，详见[测试报告](../docs/TEST_REPORT.md)。
