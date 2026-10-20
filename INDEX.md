# 实验二代码索引

代码仓库保留算法、测试、课程输入、实验方案和复现工具。实验输出在本地生成；正式报告由独立的 `../AI_Project_2/` 目录维护。

## 建议阅读顺序

1. [README：环境与运行命令](README.md)
2. [课程要求](实验二要求_new.pdf)
3. [技术规格与测试设计](docs/specification.md)
4. [最终实验方案](docs/final_experiment_protocol.md)
5. [数据来源与统计口径](docs/data_provenance.md)

## 算法与测试

| 文件 | 内容 |
|---|---|
| [src/search_algorithms/astar.py](src/search_algorithms/astar.py) | 通用A*及迷宫、加权地形入口；支持两种同分策略 |
| [src/search_algorithms/minimax.py](src/search_algorithms/minimax.py) | 完整Minimax与JSON适配 |
| [src/search_algorithms/alpha_beta.py](src/search_algorithms/alpha_beta.py) | Alpha-Beta与子节点顺序 |
| [src/search_algorithms/treasure_game.py](src/search_algorithms/treasure_game.py) | 距离矩阵、不可变状态和宝藏博弈 |
| [src/search_algorithms/models.py](src/search_algorithms/models.py) | 结果和统计数据结构 |
| [tests](tests) | 522项官方样例、边界、随机及计时方法测试 |
| [experiments/references.py](experiments/references.py) | 独立BFS、Dijkstra和动作序列穷举 |

## 实验与复现

| 文件 | 内容 |
|---|---|
| [experiments/cases.py](experiments/cases.py) | 课程输入与固定种子生成器 |
| [data/test_cases/course.json](data/test_cases/course.json) | 机器可读课程地图及宝藏价值 |
| [experiments/run_all.py](experiments/run_all.py) | 正式与快速实验的统一入口 |
| [experiments/maze_ablation.py](experiments/maze_ablation.py) | 启发函数×同分策略的2×2消融 |
| [experiments/treasure_experiments.py](experiments/treasure_experiments.py) | 宝藏深度、价值及交错计时 |
| [experiments/metrics.py](experiments/metrics.py) | 测量边界、预热和确定性执行顺序 |
| [experiments/aggregate.py](experiments/aggregate.py) | 实例中位数和分层聚合 |
| [experiments/analysis.py](experiments/analysis.py) | 因素对照、同轮配对与bootstrap区间 |
| [experiments/batch.py](experiments/batch.py) | 数据批次与文件哈希 |
| [experiments/rebuild_results.py](experiments/rebuild_results.py) | 从已有本地记录重建派生结果 |
| [experiments/plot_results.py](experiments/plot_results.py) | 生成九组图表 |
| [experiments/write_report.py](experiments/write_report.py) | 生成本地数据分析参考稿 |
| [experiments/audit_results.py](experiments/audit_results.py) | 核对源码、最优值、统计、顺序和文件哈希 |
| [experiments/verify_official.py](experiments/verify_official.py) | 四题课程样例与矩阵验收 |
| [scripts/reproduce_ci.py](scripts/reproduce_ci.py) | 独立目录及Python3.11虚拟环境复现 |
| [scripts/check_repository.py](scripts/check_repository.py) | 目录、语法、链接和实验审计 |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | GitHub Actions验证流程 |

## 文档与环境

- [接口与先行测试规格](docs/specification.md)
- [本轮测量方案及判据](docs/final_experiment_protocol.md)
- [数据来源](docs/data_provenance.md)
- [验收说明](docs/acceptance.md)
- [测试与复现说明](docs/validation_notes.md)
- [原始开发任务书](docs/task_requirements.md)
- [依赖范围](requirements.txt)、[固定依赖版本](requirements-repro.txt)、[包与pytest配置](pyproject.toml)

## 本地产物

运行实验后，`results/raw/`、`results/tables/`、`results/figures/`分别保存记录、统计和图表，`report/report.md`保存数据分析参考稿。这些目录及`docs/local_ci_validation.json`由Git忽略，不随代码提交。

用于报告写作的最终批次为`20261020T032620Z-6b476869`，完整快照和索引保存在独立报告目录的`experiment_data/`与`EXPERIMENT_INDEX.md`中。
