from math import inf
from statistics import median
import pytest
from search_algorithms import maze_search, weighted_search, AStarStats, GameStats
from experiments.cases import maze_case, weighted_case, TREASURE, VALUES
from experiments.references import bfs_distance, dijkstra_cost
from experiments.metrics import measure_interleaved, game_output, shuffled_order
from experiments.analysis import timing_tables, median_interval, ablation_tables
from experiments.treasure_experiments import timed_game
from search_algorithms import compute_distance_matrix


@pytest.mark.parametrize('seed',range(60))
def test_factorial_methods_match_bfs(seed):
    n=2+seed%16
    grid=maze_case(n,(seed%6)/10,seed)
    goal=(n-1,n-1)
    expected=bfs_distance(grid,(0,0),goal)
    for h in ('zero','manhattan'):
        for tie in ('f_h_fifo','f_fifo'):
            r=maze_search((0,0),goal,grid,heuristic=h,tie_breaking=tie)
            assert r.cost==expected
            if expected==inf:
                assert r.path==[]
            else:
                assert r.path[0]==(0,0) and r.path[-1]==goal and len(r.path)-1==expected
                assert all(grid[p[0]][p[1]]!='X' for p in r.path)
                assert all(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(r.path,r.path[1:]))
    default=maze_search((0,0),goal,grid)
    explicit=maze_search((0,0),goal,grid,tie_breaking='f_h_fifo')
    assert default.path==explicit.path
    for key in ('expanded','generated','max_frontier','popped','stale_pops'):
        assert getattr(default.stats,key)==getattr(explicit.stats,key)


@pytest.mark.parametrize('n',(2,3,10,80))
@pytest.mark.parametrize('h',('zero','manhattan'))
@pytest.mark.parametrize('tie',('f_h_fifo','f_fifo'))
def test_empty_grid_f_plateau(n,h,tie):
    r=maze_search((0,0),(n-1,n-1),maze_case(n,0,0),heuristic=h,tie_breaking=tie)
    assert r.cost==2*(n-1)
    assert r.stats.expanded==(2*(n-1) if h=='manhattan' and tie=='f_h_fifo' else n*n-1)


@pytest.mark.parametrize('seed',range(20))
def test_fifo_reopening_on_weighted_graphs(seed):
    grid=weighted_case(10,.4,seed,obstacle=.2,zero=seed%2==0)
    for tie in ('f_h_fifo','f_fifo'):
        r=weighted_search((0,0),(9,9),grid,tie_breaking=tie)
        assert r.cost==dijkstra_cost(grid,(0,0),(9,9))


def test_invalid_tie_breaking():
    with pytest.raises(ValueError,match='tie_breaking'):
        maze_search((0,0),(0,0),[['.']],tie_breaking='other')


def test_interleaved_schedule_and_warmups():
    trace=[]
    def make(method):
        def call(st):
            trace.append(method)
            st.visited_nodes=1
            st.evaluated_leaves=1
            return 7
        return call
    calls={k:make(k) for k in ('minimax','original','reverse','heuristic')}
    rows=measure_interleaved(calls,GameStats,{'case_id':'case','experiment':'treasure'},30,game_output,7)
    assert len(trace)==8+120 and len(rows)==120
    assert set(trace[:4])==set(calls) and set(trace[4:8])==set(calls)
    assert trace[8:]==[r['algorithm'] for r in rows]
    for round_id in range(30):
        group=[r for r in rows if r['round']==round_id]
        assert len(group)==4 and {r['algorithm'] for r in group}==set(calls)
        assert [r['order_index'] for r in group]==list(range(4))
        assert all(r['execution_order']=='|'.join(trace[8+round_id*4:12+round_id*4]) for r in group)
    assert len({r['execution_order'] for r in rows})>1
    assert shuffled_order(calls,'case',4)==shuffled_order(calls,'case',4)
    assert shuffled_order(calls,'case',4)[1]!=shuffled_order(calls,'other',4)[1]
    with pytest.raises(AssertionError,match='oracle mismatch'):
        measure_interleaved(calls,GameStats,{'case_id':'bad'},1,game_output,8)


def test_real_game_all_orders_interleaved():
    rows=timed_game(compute_distance_matrix(TREASURE),VALUES,4,
        {'experiment':'treasure','case_id':'official_h4','depth':4},3)
    assert len(rows)==12
    assert all(r['optimal_cost']==3 and r['best_target']=='T3' for r in rows)
    assert {r['algorithm']:r['visited_nodes'] for r in rows}=={
        'minimax':65,'original':47,'reverse':46,'heuristic':37}


@pytest.mark.parametrize('pattern',('faster','slower','uncertain'))
def test_paired_timing_statistics(pattern):
    rows=[]
    for round_id in range(30):
        baseline=1+round_id/100
        delta=-.2 if pattern=='faster' else (.2 if pattern=='slower' else (.2 if round_id%2 else -.2))
        for i,(method,time) in enumerate((('original',baseline),('reverse',baseline+.4),('heuristic',baseline+delta))):
            rows.append({'experiment':'treasure','case_id':'synthetic','depth':'4','round':str(round_id),
                'algorithm':method,'wall_ms':str(time),'order_index':str(i)})
    tables=timing_tables(rows)
    assert len(tables['treasure_timing_pairs'])==90
    s=next(r for r in tables['treasure_timing_summary'] if r['baseline']=='original' and r['candidate']=='heuristic')
    diffs=[float(r['wall_ms'])-float(rows[(i//3)*3]['wall_ms']) for i,r in enumerate(rows) if r['algorithm']=='heuristic']
    assert s['paired_median_delta_ms']==pytest.approx(median(diffs))
    assert s['conclusion']=={'faster':'stable_faster','slower':'slower','uncertain':'uncertain'}[pattern]
    assert s['paired_delta_ci_low']<=s['paired_median_delta_ms']<=s['paired_delta_ci_high']


def test_constant_block_bootstrap_and_factorial_contrasts():
    for length in (1,3):
        assert median_interval([2.]*30,seed=42,block_length=length)==(2.,2.)
    values={'zero__f_h_fifo':10,'zero__f_fifo':10,'manhattan__f_h_fifo':4,'manhattan__f_fifo':8}
    cases=[{'experiment':'maze_ablation','algorithm':m,'case_id':'c','grid_size':'10','density':'0',
        'seed':'0','reachable':'True',**{k:str(v) for k in ('expanded','generated','max_frontier','wall_ms')}}
        for m,v in values.items()]
    contrasts=ablation_tables(cases,[])['ablation_contrasts']
    expected={'heuristic_at_f_h_fifo':-6,'heuristic_at_f_fifo':-2,'tie_at_zero':0,'tie_at_manhattan':-4,'interaction':-4}
    assert {r['contrast']:r['delta'] for r in contrasts if r['metric']=='expanded'}==expected
