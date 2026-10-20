# 测试与复现说明

测试结果保存在 `results/raw/pytest.xml`，正式实验审计见 `results/raw/audit.json`。

## 官方博弈树的节点计数

从左到右访问时，Minimax遍历15个节点、评价8次叶节点；Alpha-Beta访问14个节点、评价7次叶节点，跳过1个兄弟分支。过程如下：

1. min1/max1 访问3、5，得到5，min1的beta=5。
2. min1/max2 先访问6，alpha=6>=beta=5，跳过9（唯一实际剪枝）。
3. 根alpha=5。min2/max2的beta=∞，访问6和9，得到9。
4. min2/max3的窗口[5,9]，访问1、2，得到2；min2此时无剩余兄弟可跳过。
5. 根max(5,2)=5。完整15节点/8叶，剪枝14节点/7叶/1分支。

## 本机pytest启动器

本机Windows的pytest启动器出现过DLL重定位错误，使用模块入口可正常运行：

```powershell
python -m pytest -q --junitxml=results/raw/pytest.xml
```
