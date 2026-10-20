# 最终交付验收

代码与报告分开维护：本仓库跟踪算法、测试、输入与复现工具，`results/`和`report/`由本地命令生成。用于写作的最终批次保存在独立目录`../AI_Project_2/experiment_data/20261020T032620Z-6b476869/`，入口为该目录的`EXPERIMENT_INDEX.md`。

## 已交付

- 四题实现：一个通用可重开A*；题1/2公开接口；完整Minimax、Alpha-Beta及JSON适配；六点有向距离矩阵、不可变宝藏状态、两个博弈求解入口。
- 官方回归：迷宫7步、加权成本7、树根值5、H2为T2/-1、H4为T3/3；矩阵36项由算法计算并与独立最短路径核对。
- 自动测试：522项，结果见results/raw/pytest.xml；路径、树、有向博弈及交错计时方法均有测试。
- 正式设置：320个迷宫、400个加权地图、180棵树；宝藏深度与价值敏感性每方法30轮交错测量。另在原迷宫上进行2×2消融，共13,560条测量，30次预计算/端到端计时另存。
- 统计：逐次原始CSV、实例中位数、配置均值/标准差、分可达性统计、配对缩减率及种子bootstrap区间。
- 创新：即时收益动作排序；合成树廉价估计排序；H=0..6、T1价值0..18、零权及障碍扩展。保留效果有限的对照结果。
- 文档与图表：技术规格、本轮实验方案、README、中文报告、9组PNG/SVG、课程要求与机器可读输入。
- 目录清理：删除LaTeX相关源文件、编译结果、Overleaf压缩包、旧版归档、排版截图及临时缓存；正式结果与Markdown报告保留。完整文件索引为根目录INDEX.md，数据来源见data_provenance.md。
- 一条命令：python -m experiments.run_all；运行末尾自动生成报告、检查源码哈希、重复计数、跨方法最优值、全部图表链接，并写results/raw/audit.json。
- 独立验证：GitHub Actions使用Python3.11执行完整测试、课程样例、quick复现与审计。本地独立环境记录见docs/local_ci_validation.json。

## 运行检查

```powershell
python -m pytest -q --junitxml=results/raw/pytest.xml
```

完成测试后，运行 `python -m experiments.run_all` 重建实验结果，再运行 `python scripts/check_repository.py` 检查目录、链接与结果记录。

## 研究边界

固定种子可复现节点计数与代价，时间会受运行环境影响。当前实验覆盖每配置20个随机实例和一个固定四宝藏地图，后续可扩展到真实地图和更多宝藏。
