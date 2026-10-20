# 当代人工智能 · 实验二：搜索算法

本项目实现迷宫A*、加权地形搜索、Minimax、Alpha-Beta及宝藏对抗博弈，并提供自动测试、对照实验和中文报告。核心算法只依赖Python标准库。

## 快速开始

使用 Python 3.11+，在仓库根目录运行：

```powershell
python -m pip install -r requirements.txt
python -m pytest -q --junitxml=results/raw/pytest.xml
python -m experiments.demo
python -m experiments.verify_official
python -m experiments.run_all
python -m experiments.audit_results
```

`run_all`依次运行课程样例、对照实验、数据聚合、绘图、报告生成和批次审计。当前共522项测试。从仓库直接运行即可；如需在其他目录导入算法，可先执行 `python -m pip install -e .`。

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
| 本轮实验方案与统计判据 | [docs/final_experiment_protocol.md](docs/final_experiment_protocol.md) |

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

A*默认使用 `f_h_fifo=(f,h,seq,g,pos)`。可通过 `maze_search(..., tie_breaking='f_fifo')` 改为仅按f和插入顺序排序；`astar_search`和`weighted_search`也支持该关键字。四题原有公开求解接口及默认行为保持不变。

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
  results/figures/        9组PNG和SVG（含消融及配对计时）
  docs/                   技术规格、原始任务书、数据来源与验收记录
  report/report.md        完整中文实验报告
  scripts/check_repository.py  文件链接、目录清洁与可复现性检查
  INDEX.md                分类文件索引
```

## 实验复现与图表

```powershell
python -m experiments.run_all --quick
python -m experiments.audit_results --quick
python -m experiments.run_all
python -m experiments.rebuild_results
python -m experiments.audit_results
python scripts/check_repository.py
```

quick使用较少样本，写入被Git忽略的results/quick，不覆盖正式数据或报告。正式模式保留原来的320张迷宫、400张加权地图、180棵合成树、H=0..6及T1价值配置，并在同一批320张迷宫上增加2×2消融。

最终批次共13,560条测量：基础路径/树6,480条、宝藏深度840条、价值敏感性2,400条、独立A*消融3,840条。额外30次距离预计算/端到端计时另存。测量行包含算法对照及重复计时，不能视为独立样本数。

基础路径与树实验仍为每方法3次。宝藏及T1敏感性实验先预热2轮，再按轮次交错测量4种算法，每种30次；消融也按轮次交错，每方法3次。每轮执行顺序由固定种子派生，记录在measurement_order.csv及原始测量中。wall_ms包含函数调用、输入检查和排序成本，预计算单独统计。

节点统计按实例聚合，并用1000次种子bootstrap估计区间。宝藏计时按同轮配对，提供中位数、差值、时间比，以及5000次配对/循环块bootstrap区间。H4是否稳定更快按预先声明的区间和轮次比例判断，见实验方案。

每次运行生成独立run_id；environment.json保存参数、依赖和源码SHA256，batch_manifest.json将原始数据、表格、图表及报告绑定到同批结果。审计用BFS/Dijkstra/穷举核对最优值，并从原始CSV重算统计、配对差值和执行顺序。`rebuild_results`只从本批原始文件重建所有派生结果，不重新计时。Git按字节保存冻结结果，跨系统检出后仍可验证文件哈希。固定种子可复现路径成本和节点统计，时间会随机器和调度变化。

## Python 3.11 CI与独立复现

[GitHub Actions](.github/workflows/ci.yml)自动安装requirements-repro.txt，运行完整pytest、四题样例、quick实验及输出审计。使用Python3.11在本地执行 `python scripts/reproduce_ci.py`，可在临时目录及全新虚拟环境中重复同样流程；记录保存在docs/local_ci_validation.json。

## 已知限制

输入范围为有限无环树和非负整数地形。宝藏无可达动作时直接终止，并列最优按当前顺序选择首个动作。较深递归受Python递归上限约束；排序收益随实例变化。实验使用合成地图和四宝藏场景，尚未评估大型真实地图。

若Windows的pytest启动器出现DLL错误，可使用 `python -m pytest` 运行同一套测试。
