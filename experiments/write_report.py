"""Generate the Chinese report using only persisted full-mode measurements."""
import json
from pathlib import Path
from statistics import mean, median
import xml.etree.ElementTree as ET
from search_algorithms import TreasureState, treasure_minimax, transition
from .metrics import read_csv, write_csv


def fmt(value):
    try:
        x = float(value)
        return str(int(x)) if x.is_integer() else f'{x:.3f}'
    except (ValueError, TypeError):
        return str(value)


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
        '|' + '|'.join(['---']*len(headers)) + '|',
        *['| ' + ' | '.join(fmt(x) for x in row) + ' |' for row in rows]])


def write_report(root):
    env = json.loads((root/'raw/environment.json').read_text(encoding='utf-8'))
    if env['mode'] != 'full':
        raise ValueError('formal report requires full-mode data')
    official = json.loads((root/'raw/official.json').read_text(encoding='utf-8'))
    pv = json.loads((root/'raw/principal_variations.json').read_text(encoding='utf-8'))
    summary = read_csv(root/'tables/summary.csv')
    cases = read_csv(root/'tables/per_case.csv')
    paired = read_csv(root/'tables/paired_summary.csv')
    raw = {name:read_csv(root/'raw'/f'{name}.csv') for name in ('maze','weighted','tree','treasure','sensitivity')}
    total = sum(map(len, raw.values()))
    correct = sum(r['correctness_passed']=='True' for rows in raw.values() for r in rows)
    testfile = root/'raw/pytest.xml'
    if not testfile.exists():
        raise FileNotFoundError('run pytest --junitxml=results/raw/pytest.xml before creating report')
    suites = ET.parse(testfile).getroot()
    test_count = sum(int(s.attrib.get('tests',0)) for s in suites.iter('testsuite'))
    failures = sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in suites.iter('testsuite'))
    skipped = sum(int(s.attrib.get('skipped',0)) for s in suites.iter('testsuite'))

    def select(data, **filters):
        return [r for r in data if all(str(r.get(k)) == str(v) for k,v in filters.items())]

    def one(data, **filters):
        rows = select(data, **filters)
        if len(rows) != 1:
            raise ValueError(f'expected one row for {filters}, got {len(rows)}')
        return rows[0]

    maze_rows, reach_rows = [], []
    for n in (10,20,40,80):
        for density in (0,.1,.2,.3):
            d = str(density)
            base = select(cases, experiment='maze', grid_size=n, density=d, algorithm='zero')
            count = sum(r['reachable']=='True' for r in base)
            reach_rows.append([n,d,count,len(base)-count,f'{count/len(base):.0%}'])
            if count:
                z = one(summary, experiment='maze',grid_size=n,density=d,algorithm='zero',reachable='True')
                a = one(summary, experiment='maze',grid_size=n,density=d,algorithm='manhattan',reachable='True')
                p = one(paired, experiment='maze',grid_size=n,density=d,algorithm='manhattan',reachable='True')
                maze_rows.append([n,d,count,z['expanded_mean'],a['expanded_mean'],
                    f"{float(p['reduction_mean']):.1%}",
                    f"[{float(p['reduction_ci_low']):.1%}, {float(p['reduction_ci_high']):.1%}]",
                    z['wall_ms_mean'],a['wall_ms_mean']])
    weighted_rows = []
    for scenario, high in [('base',.1),('base',.4),('base',.7),('zero',.4),('obstacles',.4)]:
        for n in (10,20,40,80):
            z = one(summary,experiment='weighted',grid_size=n,scenario=scenario,high_ratio=high,algorithm='zero',reachable='True')
            a = one(summary,experiment='weighted',grid_size=n,scenario=scenario,high_ratio=high,algorithm='adjusted',reachable='True')
            p = one(paired,experiment='weighted',grid_size=n,scenario=scenario,high_ratio=high,algorithm='adjusted',reachable='True')
            weighted_rows.append([scenario,high,n,z['instances'],z['optimal_cost_mean'],z['path_steps_mean'],a['path_steps_mean'],
                                  z['expanded_mean'],a['expanded_mean'],f"{float(p['reduction_mean']):.1%}",
                                  z['wall_ms_mean'],a['wall_ms_mean']])
    tree_rows = []
    for branch in (2,3,4):
        for depth in (2,4,6):
            for method in ('minimax','original','reverse','heuristic'):
                r = one(summary,experiment='tree',branch=branch,depth=depth,algorithm=method)
                tree_rows.append([branch,depth,method,r['visited_nodes_mean'],r['evaluated_leaves_mean'],
                                  r['cutoff_events_mean'],r['pruned_siblings_mean'],r['ordering_probes_mean'],r['wall_ms_mean']])
    game_rows = []
    for depth in range(7):
        for method in ('minimax','original','reverse','heuristic'):
            r = one(cases,experiment='treasure',depth=depth,algorithm=method)
            game_rows.append([depth,method,r['best_target'] or 'None',r['optimal_cost'],r['visited_nodes'],
                              r['evaluated_leaves'],r['cutoff_events'],r['pruned_siblings'],r['wall_ms']])
    sensitivity_rows=[]
    for value in range(0,19,2):
        rs = [one(cases,experiment='sensitivity',t1_value=value,depth=d,algorithm='original') for d in (2,4)]
        sensitivity_rows.append([value,rs[0]['best_target'],rs[0]['optimal_cost'],rs[1]['best_target'],rs[1]['optimal_cost']])
    matrix = official['distance_matrix']
    labels = list(matrix)
    matrix_table = table(['起点/终点',*labels],[[a,*[matrix[a][b] for b in labels]] for a in labels])
    roots=read_csv(root/'raw/root_actions.csv')
    root_table=table(['首步','H=2','H=4'], [[t,one(roots,depth=2,target=t)['value'],one(roots,depth=4,target=t)['value']]
                                           for t in ('T1','T2','T3','T4')])
    variations=[]
    for depth in ('2','4'):
        for step,r in enumerate(pv[depth],1):
            variations.append([depth,step,r['player'],r['target'],r['gain'],r['score_a'],r['score_b'],r['score_a']-r['score_b']])
    # Tabulate every B reply after each A root action, using exact full-window minimax.
    responses=[]
    from .cases import VALUES
    for depth in (2,4):
        for target in sorted(VALUES):
            s = transition(TreasureState(),target,matrix,VALUES)
            for reply in sorted(s.remaining):
                child = transition(s,reply,matrix,VALUES)
                result = treasure_minimax(child,depth-2,matrix,VALUES)
                responses.append({'depth':depth,'a_first':target,'b_reply':reply,'utility':result['best_value']})
    write_csv(root/'tables/root_responses.csv',responses)
    times=read_csv(root/'raw/routing_times.csv')
    pre=median(float(r['precompute_ms']) for r in times)
    end=median(float(r['end_to_end_ms']) for r in times)
    mm4=one(cases,experiment='treasure',depth=4,algorithm='minimax')
    ab4=one(cases,experiment='treasure',depth=4,algorithm='original')
    heur4=one(cases,experiment='treasure',depth=4,algorithm='heuristic')
    z80=one(summary,experiment='maze',grid_size=80,density='0',algorithm='zero',reachable='True')
    a80=one(summary,experiment='maze',grid_size=80,density='0',algorithm='manhattan',reachable='True')
    b4mm=one(summary,experiment='tree',branch=4,depth=6,algorithm='minimax')
    b4ab=one(summary,experiment='tree',branch=4,depth=6,algorithm='original')
    b4heur=one(summary,experiment='tree',branch=4,depth=6,algorithm='heuristic')
    weighted80=one(paired,experiment='weighted',grid_size=80,scenario='base',high_ratio=.4,algorithm='adjusted',reachable='True')
    s80=one(summary,experiment='weighted',grid_size=80,scenario='zero',high_ratio=.4,algorithm='adjusted',reachable='True')
    report = f'''# 当代人工智能实验二：搜索算法

## 摘要

本实验实现四方向迷宫A*、加权A*、Minimax、Alpha-Beta及宝藏对抗博弈。核心搜索使用Python标准库编写，以独立BFS、Dijkstra和动作序列穷举交叉验证。自动测试共{test_count}项，失败{failures}项、跳过{skipped}项；完整实验保存{total}次测量，最优值核对{correct}/{total}一致。

在80×80无障碍迷宫中，零启发式平均扩展 {fmt(z80['expanded_mean'])} 个节点，曼哈顿为 {fmt(a80['expanded_mean'])} 个；该结果受到明确的 (f,h,序号) 排序影响。加权地图因 E 免费而采用 max(d-1,0)×w_min，80×80、40%高权场景的配对扩展减少率为 {float(weighted80['reduction_mean']):.1%}。四分支六层合成树中，Minimax 平均访问 {fmt(b4mm['visited_nodes_mean'])} 节点，原始顺序 Alpha-Beta 为 {fmt(b4ab['visited_nodes_mean'])}。宝藏博弈的 H=2 得 T2/-1，H=4 得 T3/3。即时收益排序在官方 H=4 中访问 {fmt(heur4['visited_nodes'])} 节点，原始剪枝为 {fmt(ab4['visited_nodes'])}；是否节省时间应与排序开销共同判断。结论仅覆盖本实验分布和规模。

## 1. 实验目标与需求依据

四题依次研究单位边权下的启发式搜索、非均匀边权下的代价最优性、对抗环境中的效用回传与剪枝，以及路径代价对长期策略的影响。题1、题2和题4的距离计算共用一个A*核心；题3以完整递归Minimax作为剪枝对照。题4另用动作序列穷举独立计算得分和效用，与两种搜索结果交叉核对。

课程PDF第3–7页给出迷宫和加权地形，第8–13页给出博弈树，第14–15页给出宝藏地图与收益，第16–17页说明报告要求和评分标准。题2进入E免费；题4的A、B和宝藏格进入成本均为1。接口约定与测试设计见 `../docs/specification.md`。

## 2. 数学建模、算法与正确性

### 2.1 单位代价迷宫

状态 s=(row,col)，动作集合为上、下、左、右，越界或 X 无后继。每条合法边代价为1；g(start)=0，g(v)=g(u)+1。启发式 h(s)=|row-row_E|+|col-col_E|，f=g+h。任何四邻接路径至少需要曼哈顿距离这么多步，障碍只能增加必要路程，所以 h 可采纳。相邻格的曼哈顿差至多1，h(u)≤1+h(v)，因此一致。

开放列表用 heapq，条目为 (f,h,递增序号,g,坐标)。同 f 优先较小 h，最后用插入序号稳定消歧；邻居始终按上、下、左、右。所有 h0/启发式对照采用同一规则，但 h 的改变也会改变次级排序值，所以本文比较的是固定排序规则下完整搜索策略的效果。g_score保存目前最优已知代价；只在严格改进时更新父指针并重新入队。弹出的旧g不等于当前g时跳过。目标正式出队后逆向追溯 came_from 并反转，不将目标计入 expanded。无解时队列耗尽，路径为空、内部cost=∞。

算法不把首次发现视为最优，也不设置永久禁止重开的 closed 集。若 h 可采纳、h(goal)=0，较优候选路径上必有 f 不大于真正最优代价的前沿节点；因此不可能先取出更贵的目标并结束。重开使这一论证不依赖一致性；一致性则减少重复展开。零权环通过“严格降低g才更新”避免相等代价反复入队。随机测试还用不一致但可采纳的启发式检验更新与过期条目。

### 2.2 加权地形与免费终点

边权 c(u,v)=w(v)，不计起点初始权，目标进入权明确为0。公共接口返回最小整数代价；不可达 -1。内部保留路径用于逐步重算。非法负权会破坏本实现的最优性前提，直接拒绝；零权普通地形作为拓展支持。

普通曼哈顿在距离E一格时为1，而真实剩余代价为0，会高估成本。因此采用 h(s)=max(Manhattan(s,E)-1,0)×w_min。距离为d的路径至少包含d-1条进入非终点的边，每条至少花费w_min，因此该式是剩余代价的下界。非终点相邻边的h降幅至多w_min≤c(u,v)；进入E时两端h均为0，满足一致性。存在普通零权时，w_min=0，算法退化为Dijkstra。

S 若被重新进入，其成本按普通数字格最小权处理；初始累计依旧为0。该行为只涉及 PDF 未定义的扩展回访，在非负最优简单路径中不影响课程结果。端点坐标为权威；S/E存在时必须匹配且唯一；纯数字网格也可用，指定goal免费。输入不修改，正常不可达与 ValueError 区分。

### 2.3 Minimax 与 Alpha-Beta

叶值 V(n)=value(n)，MAX取子值最大值，MIN取最小值。根为 MAX，每层交替；默认严格从左到右。不以 value 的真假判断叶子，数值0是合法叶值。共享 max2 子树按两次引用分别遍历。

Alpha 表示MAX已经保证的下界，Beta表示MIN已经保证的上界。MAX更新 best及alpha，MIN更新best及beta；当 alpha≥beta，祖先已存在至少同样好的选择，当前剩余兄弟即使改变此子树的精确值也无法改善根决策，因此可跳过。内部 fail-soft 返回值可能只代表界；实现不把剪枝返回值作为精确缓存。根完整窗口的最终值与 Minimax 一致。

访问顺序决定边界建立的早晚，从而影响访问量，同深度的最优效用保持一致。最坏顺序下叶子数量仍为b^d，理想排序可使搜索量接近b^(d/2)。实验中的排序用各子树最左叶值作估计，探测次数单独记录，排序耗时计入总时间。

### 2.4 宝藏状态与效用

不可变状态为 (pos_a,pos_b,remaining,score_a,score_b,current_player)。每次动作选择一个剩余且可达的宝藏，gain=Vi-d(pos,Ti)，允许负数；仅改变行动者位置和得分，移除该宝藏并切换玩家。另一玩家不阻挡，路过其他宝藏不领取，已获取格可继续通过。A最大化、B最小化 U=Score_A-Score_B。

六标签之间分别计算两个方向，共运行30次A*，对角为0。课程六个端点的进入权均为1，因此本例矩阵对称。H表示宝藏选择次数：H=2是A、B各一次，H=4是完整A→B→A→B。H=0、宝藏耗尽或当前无合法动作时，以当前U评价。并列最优时取访问顺序中的首个动作，因此不同排序可能选出不同的并列首步，但最优效用相同。

## 3. 实验环境、指标与统计方法

- Python：`{env['python'].splitlines()[0]}`。
- 系统：`{env['platform']}`；处理器：`{env['processor']}`；逻辑处理器数：{env['logical_cpus']}。
- 依赖：pytest {env['dependencies']['pytest']}；Matplotlib {env['dependencies']['matplotlib']}。核心算法只用标准库，不用NetworkX等成品搜索实现。
- 随机实例：每组种子0–19；每个实例使用局部 random.Random(seed)，原始CSV保存种子、规模及生成参数。
- 迷宫：10/20/40/80方格，障碍概率0/10%/20%/30%，共320张地图。障碍独立采样，仅强制起终点可通行；不筛掉难例、不补抽可达样本。
- 加权：四种规模，8权概率10%/40%/70%，其余均匀选1或3；额外40%高权配普通0/1/3的零权场景及20%障碍场景，共400张地图。数字地形在非障碍格采样，端点覆盖为S/E。
- 树：分支2/3/4、深度2/4/6，各20棵，叶值均匀整数[-100,100]，共180棵，输入树生成不计入搜索时间。
- 每实例每方法预热一次，再测3次；宝藏固定地图及敏感性测30次。随机实例的方法执行顺序按种子固定打乱。输入相同、算法版本和测量边界相同。
- runtime_ms为perf_counter记录算法主体，wall_ms包含调用包装和输入检查；图表与表格中“时间”统一使用 wall_ms，排序成本包含其中。先对同实例重复时间取中位数，再跨种子计算均值/标准差。
- bootstrap对独立实例重采样1000次，种子20261019，以2.5%/97.5%近似分位数估计均值95%区间。方法对比先计算每实例节点减少比例，再对配对比例做bootstrap。重复计时在实例内聚合；固定宝藏的30次重复用于估计计时波动。
- A* generated包含初始和重新入队；popped包含过期；expanded不含目标；max_frontier为堆条目峰值；stale_pops单独保存。博弈visited包含根和叶；evaluated_leaves仅终止评价；cutoff是实际跳过剩余兄弟的事件；pruned_siblings只是同层跳过数，不能直接当总减少节点数。排序额外探测量为ordering_probes。

原始记录共{total}条（另有30次距离与端到端计时）。`results/raw`保存所有重复数据和环境，`tables/per_case.csv`保存实例中位数，`summary.csv`按配置及可达性分组，`paired_summary.csv`保存配对减少率和区间。不可达实例的最优成本∞不进入有限路径成本均值，节点/时间仍完整保留在不可达分层。整个实验及聚合用时{env['experiment_elapsed_seconds']:.2f}秒，未包含后续绘图和报告生成。

## 4. 正确性验证

验收记录：{test_count}项测试，{test_count-failures-skipped}通过，{failures}失败，{skipped}跳过。JUnit见 `../results/raw/pytest.xml`。覆盖官方样例、同点/相邻/单行列、多解/死胡同/密集障碍/无解、负权/零权/错配标识、空/不矩形/越界、共享子树/负数与零叶、较深单链、不平衡树、冻结状态、不可达宝藏、深度零及超过宝藏数量等。

随机正确性测试包括100个迷宫与BFS对照、100个加权图与独立Dijkstra对照、100棵树与完整Minimax对照，以及60个随机有向代价博弈在H=1..4与动作序列穷举对照。路径逐段检查四邻接和可通行性，再重算成本。性能实验也逐条核对最优值，共{correct}/{total}一致。

课程样例结果为：题1最短7步；题2最小代价7；题3两算法均返回5；题4矩阵全项与独立Dijkstra一致，H2为T2/-1、H4为T3/3。节点计数的逐步推导见 `../docs/validation_notes.md`。

## 5. 题目一：最短路径与启发式效果

程序所得官方路径为：

`{official['maze_path']}`

路径总计7步，沿顶行到达(1,2)，经(1,3)、(1,4)进入右侧通道，再到(3,4)。各步均满足四邻接并避开X，长度与BFS结果一致。

可达样本数（不丢弃不可达实例）：

{table(['规模','障碍概率','可达','不可达','可达率'],reach_rows)}

下表只比较同一批可达地图，扩展数为种子均值，减少率为逐实例配对比例均值；完整不可达组数据在summary中。

{table(['规模','障碍概率','n','h0扩展','曼哈顿扩展','配对减少','95%区间','h0时间ms','A*时间ms'],maze_rows)}

![迷宫规模与扩展数量](../results/figures/maze_scaling.png)

空网格中大量格子的f相同。较小h优先使A*沿接近目标的路线前进，h0则按g逐层扩散，因此无障碍大网格中的差异明显。障碍迫使绕行时，曼哈顿距离无法反映墙体结构，搜索仍会进入看似接近目标的死路。不可达实例需要穷尽起点可达区域，通常节省较少，因此与可达实例分开统计。两种方法在所有验证输入上的最优距离一致。

计时包含网格校验。当搜索本身很短时，输入扫描可能占主要时间，因此节点缩减幅度与时间加速幅度并不相同。过期条目、重开和同分排序也会影响开销；原始数据同时保存了路径长度、generated和frontier等指标。

## 6. 题目二：代价最优与启发式修正

官方路径：`{official['weighted_path']}`。

累计进入成本为1→2→3→4→5→6→7→7，起点初始成本为0，最后进入E免费，总成本7。若把E按1收费，结果会变为8；直接使用题1的曼哈顿距离，也会在E的相邻格高估剩余成本。

各配置的可达组结果如下。base为普通地形，zero加入普通零权，obstacles加入20%障碍；高权概率表示数字格取8的概率。同一成本可能对应不同步数，表中同时列出两项指标。

{table(['场景','高权概率','规模','n','最优成本均值','h0步数','A*步数','h0扩展','A*扩展','减少率','h0时间ms','A*时间ms'],weighted_rows)}

![加权搜索开销](../results/figures/weighted_scaling.png)

![官方加权路径](../results/figures/weighted_path.png)

加权搜索最小化累计进入成本。例如测试地图第一行[S,8,E]、第二行[1,1,1]，直接走2步的成本为8，绕行4步的成本为3，算法选择后者。

普通正权场景使用w_min=1。大量3/8权格使几何下界与实际剩余代价相差较大，搜索量缩减通常小于单位代价空迷宫。80×80且40%高权场景的配对扩展减少率为{float(weighted80['reduction_mean']):.1%}，95%区间为[{float(weighted80['reduction_ci_low']):.1%}, {float(weighted80['reduction_ci_high']):.1%}]。零权场景中w_min=0，两种方法的启发值与节点数相同；80×80时adjusted平均扩展{fmt(s80['expanded_mean'])}。此时观察到的时间差主要来自调用开销和计时波动。

## 7. 题目三：值回传、剪枝过程与访问顺序

三个MAX子树值分别为max(3,5)=5、max(6,9)=9、max(1,2)=2；两个MIN分支为min(5,9)=5与min(9,2)=2；根取max(5,2)=5。中间max2被两个父节点引用，完整搜索会各遍历一次，因此共评价8次叶节点，其中6和9各两次。

从左到右搜索时，左MIN先得到5，令beta=5；其第二个MAX先看6，alpha=6≥beta=5，剩余9被剪去。根随后alpha=5；右MIN的max2需访问6和9，max3在窗口[5,9]下访问1和2，返回2。完整搜索访问15个节点、评价8次叶节点；剪枝后为14个节点、7次叶评价，节省1个分支。

合成树各配置20个独立种子的均值如下，时间为实例中位数的均值：

{table(['b','深度','方法','访问节点','评价叶','剪枝事件','跳过兄弟','排序探测','时间ms'],tree_rows)}

![合成树深度与访问节点](../results/figures/tree_scaling.png)

四分支六层的完整访问数为(4^7-1)/3=5461，与Minimax实测均值{fmt(b4mm['visited_nodes_mean'])}一致。原始AB平均访问{fmt(b4ab['visited_nodes_mean'])}个节点，最左叶估计排序访问{fmt(b4heur['visited_nodes_mean'])}个；对应平均时间为{fmt(b4mm['wall_ms_mean'])}、{fmt(b4ab['wall_ms_mean'])}、{fmt(b4heur['wall_ms_mean'])}毫秒。排序减少递归访问，同时增加估值探测，因此需要结合两类计数和时间评价。原始与反向顺序的差异取决于高值或低值在树中的分布。

## 8. 题目四：距离、深度与策略变化

实际30次有向A*输出的距离矩阵为：

{matrix_table}

该矩阵由A*按地图计算，并用独立Dijkstra逐项核对。六个端点进入代价相同，使本例距离对称。A到T2花费4、收益2，到T3花费8、收益-1；首步决策还需考虑B的反制及双方后续位置。

精确根动作值（每个动作单独完整窗口搜索，不把跨分支剪枝界误当精确值）：

{root_table}

![不同首步的精确对抗收益](../results/figures/root_actions.png)

两层只看A拿一个与B拿一个。T2带来A收益2，B通常拿T3收益3，所以效用-1；若A拿T3，A当前-1，B最佳可拿T1收益1，得到-2。四层纳入第二次行动，T3虽然首步收益低，却改变了自己后续移动位置并剥夺了B的低成本高收益目标，因此最终价值3超过T2的1。

下面逐一列出B对每个A首步的回复，后续由双方最优行动，B选择其中最小值：

{table(['H','A首步','B回复','后续最优效用'],[[r['depth'],r['a_first'],r['b_reply'],r['utility']] for r in responses])}

默认顺序下的一条完整最优对抗轨迹如下；并列时可能有另一条同效用轨迹：

{table(['H','步','玩家','宝藏','本次收益','累计A','累计B','当前U'],variations)}

H4中，T3虽然首步收益为负，却通过后续位置和剩余宝藏组合获得更高的最终效用。H2在两次选择后评价，H4在四次选择后评价，因此最优首步会随评价时点改变。

完整搜索及三种剪枝顺序对照（固定地图，30次计时取中位数；H1/H3/H0/H5/H6为自设扩展）：

{table(['H','方法','首步','效用','访问节点','评价叶','剪枝事件','跳过兄弟','时间ms'],game_rows)}

![宝藏深度与搜索开销](../results/figures/treasure_search.png)

无剪枝节点数H2为1+4+12=17，H4为1+4+12+24+24=65，与程序计数一致。H>4时宝藏取完即终止，所以节点和值不再增加。默认H4从{fmt(mm4['visited_nodes'])}降到{fmt(ab4['visited_nodes'])}节点，收益和首步仍为T3/3；不同顺序的剪枝次数不应直接换算为减少的节点总数。

计时分解：30次独立测量中，六点距离预计算中位数{pre:.3f}ms；H4默认AB仅博弈调用中位数{float(ab4['wall_ms']):.3f}ms；包含预计算的端到端中位数{end:.3f}ms。各项分别测量，中位数不要求严格可加。固定小博弈上距离计算占有显著成本，单纯优化递归未必明显改变端到端耗时。

## 9. 创新与自设拓展

### 9.1 即时收益排序的成本与收益

为更早建立剪枝边界，按Vi-d(pos,Ti)从大到小访问目标。A优先尝试提高U的动作，B优先提高自身得分、从而降低U；双方都按自己的即时gain降序。排序只改变访问顺序，终止评价仍为Score_A-Score_B。

H4原始AB访问{fmt(ab4['visited_nodes'])}个节点，排序后为{fmt(heur4['visited_nodes'])}个，减少{(1-float(heur4['visited_nodes'])/float(ab4['visited_nodes'])):.1%}；两者中位时间为{float(ab4['wall_ms']):.4f}与{float(heur4['wall_ms']):.4f}ms。排序耗时计入wall/runtime，额外探测保存在CSV中。H2和价值敏感性场景也采用同样对照，各方法的效用均与穷举一致。

合成树按最左叶值估计子树价值，宝藏博弈按即时收益排序，两者使用的信息不同。对照表同时保留节点和时间结果，便于判断排序成本是否抵消剪枝收益。后续可进一步评估置换表对重复状态的利用。

### 9.2 宝藏价值敏感性

保持地图、T2/T3/T4价值和收益规则不变，仅将T1价值设为0,2,…,18，分别比较H2/H4；每配置两种排序、各30次计时，仍以独立穷举验证。结果如下：

{table(['T1价值','H2首步','H2效用','H4首步','H4效用'],sensitivity_rows)}

![T1价值与策略变化](../results/figures/sensitivity.png)

T1价值同时影响A的抢夺收益和B的反制选择，因此最优效用呈非单调变化。偶数取值扫描显示了策略切换的大致区间；更精细的临界点可通过加密取值继续分析。并列动作按固定顺序处理，比较策略时同时观察首步目标和根效用。

### 9.3 零权与不可达扩展

普通零权使调整启发式退化到h=0；20%障碍场景则检验加权绕行和无解处理。路径不可达时返回无解，宝藏当前无合法动作时以当前效用结束。课程地图中各宝藏均可达。

## 10. 总结、局限与复现

四题实验表明：免费终点需要修正启发函数，累计代价与步数对应不同目标，访问顺序通过边界建立时机影响剪枝效率，而搜索深度会改变位置和剩余宝藏的长期价值。对照数据也显示，零权地形中启发式会退化，小型博弈树的剪枝收益可能有限。

实验每配置使用20个种子，地图来自独立随机生成，博弈树采用随机叶值，宝藏部分固定为四个目标。结果主要描述这些分布下的表现，后续可加入走廊、房间等结构化地图及更多宝藏。短调用的时间受进程调度和输入校验影响；低可达率配置的置信区间也更不稳定。本次记录开放列表条目峰值，尚未测量内存字节峰值。

复现（在project2目录）执行：

```powershell
python -m pip install -r requirements.txt
python -m pytest -q --junitxml=results/raw/pytest.xml
python -m experiments.run_all
```

`python -m experiments.demo --task 1/2/3/4`分别运行四题（实际参数选一个数字）；`python -m experiments.plot_results`仅从已保存结果重绘；`python -m experiments.write_report`仅更新本报告。quick模式输出到results/quick，不覆盖正式结果或报告。计时每次运行会变化，确定性路径、最优值、节点数、种子和生成策略可复现。

### 交付与评分要求映射

|要求|实现/证据|
|---|---|
|代码完整与状态正确|src/search_algorithms，公开四题接口；tests独立基准|
|性能评估|raw五类CSV、summary/paired_summary及7张PNG/SVG|
|算法与报告分析|第2节理论、第5–8节逐题实测与具体决策解释|
|创新与拓展|即时收益排序、合成树排序、价值/深度/零权敏感性|
|第三方复现|README、requirements、pyproject、统一run_all入口|

题目定义来自课程PDF和任务书。输入来源、随机生成方式及测量记录的统计口径见 `../docs/data_provenance.md`，表格和图表均由仓库中的实验结果生成。
'''
    folder = root.parent/'report'
    folder.mkdir(exist_ok=True)
    (folder/'report.md').write_text(report,encoding='utf-8')


if __name__ == '__main__':
    write_report(Path(__file__).resolve().parents[1]/'results')
