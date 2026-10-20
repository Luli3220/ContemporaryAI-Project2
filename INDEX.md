# 实验二文件索引

本仓库对应当代人工智能实验二：搜索算法。保留完整代码、419项测试、可复现实验和正式数据，报告使用Markdown。

## 建议阅读顺序

1. [README：环境与运行命令](README.md)
2. [完整中文实验报告](report/report.md)
3. [技术规格与测试设计](docs/specification.md)
4. [数据来源和8,520条记录的统计口径](docs/data_provenance.md)
5. [交付验收记录](docs/acceptance.md)与[验证过程说明](docs/validation_notes.md)

## 分类导航

| 目录或文件 | 内容与用途 |
|---|---|
| [实验二要求_new.pdf](实验二要求_new.pdf) | 课程原始要求，包含四题定义与评分细则 |
| [docs/task_requirements.md](docs/task_requirements.md) | 用户提供的完整开发任务书 |
| [src/search_algorithms](src/search_algorithms) | 通用A*、迷宫/加权包装、Minimax、Alpha-Beta、宝藏状态及指标模型 |
| [tests](tests) | 官方样例、边界、不变量及独立基准交叉验证 |
| [experiments/cases.py](experiments/cases.py) | 官方输入与固定种子数据生成器 |
| [experiments/references.py](experiments/references.py) | 独立BFS、Dijkstra和动作序列穷举 |
| [experiments/run_all.py](experiments/run_all.py) | 全部正式实验的统一入口 |
| [experiments/aggregate.py](experiments/aggregate.py) | 实例中位数、分层聚合与配对bootstrap统计 |
| [experiments/plot_results.py](experiments/plot_results.py) | 从已有数据生成图表 |
| [experiments/write_report.py](experiments/write_report.py) | 从正式结果重建Markdown报告 |
| [experiments/audit_results.py](experiments/audit_results.py) | 源码哈希、最优值、重复测量和图表审计 |
| [data/test_cases/course.json](data/test_cases/course.json) | 机器可读官方地图与宝藏价值 |
| [results/raw](results/raw) | 每次实际运行的原始CSV、环境、JUnit、官方结果及审计 |
| [results/tables](results/tables) | 每实例中位数、配置聚合、配对统计与根动作回复表 |
| [results/figures](results/figures) | 七组正式PNG及SVG图表 |
| [scripts/check_repository.py](scripts/check_repository.py) | 目录清洁、Python语法、Markdown链接及正式数据审计 |
| [requirements.txt](requirements.txt) | 安装所需依赖范围 |
| [requirements-repro.txt](requirements-repro.txt) | 交付实测采用的直接依赖精确版本 |
| [pyproject.toml](pyproject.toml) | 包安装和pytest搜索路径配置 |

## 原始结果入口

| 文件 | 含义 |
|---|---|
| [official.json](results/raw/official.json) | 四题官方样例、实际路径与距离矩阵 |
| [maze.csv](results/raw/maze.csv) | 迷宫两种启发式，1,920条测量 |
| [weighted.csv](results/raw/weighted.csv) | 加权地形两种启发式，2,400条测量 |
| [tree.csv](results/raw/tree.csv) | 完整Minimax与三种Alpha-Beta顺序，2,160条测量 |
| [treasure.csv](results/raw/treasure.csv) | 固定宝藏H=0..6，840条测量 |
| [sensitivity.csv](results/raw/sensitivity.csv) | T1价值敏感性，1,200条测量 |
| [routing_times.csv](results/raw/routing_times.csv) | 另存的30次预计算/端到端计时 |
| [root_actions.csv](results/raw/root_actions.csv) | 各深度各首步的精确对抗评价 |
| [principal_variations.json](results/raw/principal_variations.json) | H2/H4的一条最优对抗轨迹 |
| [environment.json](results/raw/environment.json) | 运行环境、参数、种子和源文件SHA256 |
| [pytest.xml](results/raw/pytest.xml) | 实际执行的JUnit测试记录 |
| [audit.json](results/raw/audit.json) | 正式原始结果审计结论 |

## 正式图表

| 研究问题 | PNG | SVG |
|---|---|---|
| 迷宫规模与扩展数 | [预览](results/figures/maze_scaling.png) | [矢量](results/figures/maze_scaling.svg) |
| 加权地形与启发式 | [预览](results/figures/weighted_scaling.png) | [矢量](results/figures/weighted_scaling.svg) |
| 官方加权路径 | [预览](results/figures/weighted_path.png) | [矢量](results/figures/weighted_path.svg) |
| 博弈树规模与顺序 | [预览](results/figures/tree_scaling.png) | [矢量](results/figures/tree_scaling.svg) |
| H2/H4根动作评价 | [预览](results/figures/root_actions.png) | [矢量](results/figures/root_actions.svg) |
| 宝藏搜索开销 | [预览](results/figures/treasure_search.png) | [矢量](results/figures/treasure_search.svg) |
| T1价值敏感性 | [预览](results/figures/sensitivity.png) | [矢量](results/figures/sensitivity.svg) |

正式数据不包含快速模式输出、缓存、LaTeX源文件、编译产物或旧版归档。
