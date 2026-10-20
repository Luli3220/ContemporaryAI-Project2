# 当代人工智能 · 实验二：搜索算法

本项目实现迷宫A*、加权地形搜索、Minimax、Alpha-Beta及宝藏对抗博弈，并提供自动测试、对照实验和中文报告。核心算法只依赖Python标准库。

## 快速开始

使用 Python 3.11+，在仓库根目录运行：

```powershell
python -m pip install -r requirements.txt
python -m pytest -q --junitxml=results/raw/pytest.xml
python -m experiments.demo
python -m experiments.run_all
```

`run_all`依次运行课程样例、对照实验、数据聚合、绘图和报告生成。当前测试共419项，全部通过。从仓库直接运行即可；如需在其他目录导入算法，可先执行 `python -m pip install -e .`。

正式结果已保存在仓库内，可以直接阅读 [实验报告](report/report.md)。报告会读取JUnit中的测试结果，首次复现时请先运行上面的测试命令。

## 阅读索引

| 内容 | 入口 |
|---|---|
| 完整文件索引 | [INDEX.md](INDEX.md) |
| 中文实验报告 | [report/report.md](report/report.md) |
| 课程原始要求 | [实验二要求_new.pdf](实验二要求_new.pdf) |
| 技术规格与先行测试设计 | [docs/specification.md](docs/specification.md) |
| 数据来源、实例数与测量口径 | [docs/data_provenance.md](docs/data_provenance.md) |
| 验收与环境限制 | [docs/acceptance.md](docs/acceptance.md) |
| 官方样例实测结果 | [results/raw/official.json](results/raw/official.json) |
| 原始记录审计 | [results/raw/audit.json](results/raw/audit.json) |

仓库保留Markdown报告、代码、测试、正式实验数据和图表。

## 分题运行

```powershell
python -m experiments.demo --task 1
python -m experiments.demo --task 2
python -m experiments.demo --task 3
python -m experiments.demo --task 4
```

题1返回含起终点的最短路径；题2返回最小整数成本；题3返回Minimax和Alpha-Beta结果；题4输出完整6×6距离矩阵及H=2/H=4的两算法结果。官方输入保存在 `data/test_cases/course.json`，也可用如下命令重建：

```powershell
python -m experiments.generate_cases --output data/test_cases/course.json
python -m experiments.generate_cases --kind maze --size 40 --density 0.2 --seed 3
python -m experiments.generate_cases --kind weighted --size 20 --high 0.4 --seed 7
```

## 公共接口

```python
from search_algorithms import (
    solve_maze, solve_weighted_terrain, TreeNode, minimax, alpha_beta,
    compute_distance_matrix, solve_treasure_game,
)

path = solve_maze((0, 0), (0, 1), [['S', 'E']])  # [(0,0),(0,1)]
cost = solve_weighted_terrain((0, 0), (0, 1), [['S', 'E']])  # 0
value = alpha_beta(TreeNode(children=[TreeNode(0), TreeNode(-2)]))  # 0
```

详细路径与统计用 `maze_search/weighted_search` 返回的PathResult。`AStarStats`和`GameStats`可通过stats参数传入；每次调用自动重置。题3支持JSON适配器tree_from_json。题4支持不可变TreasureState、transition，以及可复用距离矩阵的treasure_minimax/treasure_alpha_beta，两者返回best_target/best_value字典。

重要约定：题2进入goal免费，题4关键标签进入成本为1；负权非法；零权安全退化到h=0；默认树访问左到右。合法无解与非法输入分开处理。S/E出现时应与指定坐标匹配，坐标从0开始。完整数学说明与输入扩展见 [技术规格](docs/specification.md)。

## 目录

```text
project2/
  src/search_algorithms/   通用A*、题1/2包装、Minimax、AB、宝藏状态与求解
  tests/                  官方/边界/随机/不变量测试
  experiments/            固定生成、独立BFS/Dijkstra/排列穷举、测量、聚合、图表、报告
  data/test_cases/        机器可读官方输入
  results/raw/            每次重复测量CSV、官方JSON、环境、JUnit
  results/tables/         每实例中位数、配置聚合、配对减少率、各B回复
  results/figures/        7张PNG和对应SVG
  docs/                   技术规格、原始任务书、数据来源与验收记录
  report/report.md        完整中文实验报告
  scripts/check_repository.py  文件链接、目录清洁与可复现性检查
  INDEX.md                分类文件索引
```

## 实验复现与图表

```powershell
python -m experiments.run_all --quick
python -m experiments.run_all
python -m experiments.plot_results
python -m experiments.write_report
python -m experiments.audit_results
python scripts/check_repository.py
```

quick仅验证实验流水线，使用较少样本并写入results/quick，不覆盖正式数据/报告；该目录由Git忽略，不随仓库提交。正式模式包含320张迷宫、400张加权地图、180棵合成树、H=0..6宝藏搜索及T1价值敏感性。每组20种子0–19；搜索预热后每方法测3次，固定宝藏测30次；跨方法输入配对。全部生成配置保存在CSV，`generate_cases`可复原任何地图。8,520条记录包含算法对照和重复计时，不是8,520个独立实例。

先在实例内取重复时间中位数，再跨种子统计；bootstrap使用固定种子20261019、1000次独立实例重采样。不可达实例保留，分层聚合。报告中的时间为包含输入校验的wall_ms；runtime_ms为搜索主体；预计算与端到端另存routing_times.csv。所有方法都计入排序成本。测试、图表、文件写入不计入搜索时间。

CSV保存种子、实例编号、算法配置、搜索计数、时间和正确性结果。environment.json记录运行环境及源码SHA256；完整运行末尾会核对重复计数、跨方法最优值和图表链接，输出audit.json。固定种子可复现路径成本和节点统计，时间会随运行环境变化。

## 已知限制

输入范围为有限无环树和非负整数地形。宝藏无可达动作时直接终止，并列最优按当前顺序选择首个动作。较深递归受Python递归上限约束；排序收益随实例变化。实验使用合成地图和四宝藏场景，尚未评估大型真实地图。

若Windows的pytest启动器出现DLL错误，可使用 `python -m pytest` 运行同一套测试。
