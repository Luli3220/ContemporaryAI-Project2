"""Standalone official regression validation, also used by CI and run_all."""
import json
from .demo import official_results
from .cases import TREASURE, MAZE, WEIGHTED
from .references import bfs_distance, dijkstra_cost


def verify(result=None):
    r = official_results() if result is None else result
    path = r['maze_path']
    assert tuple(path[0])==(0,0) and tuple(path[-1])==(3,4)
    assert len(path)-1==bfs_distance(MAZE,(0,0),(3,4))==7
    for a,b in zip(path,path[1:]):
        assert abs(a[0]-b[0])+abs(a[1]-b[1])==1 and MAZE[b[0]][b[1]]!='X'
    assert r['weighted_cost']==dijkstra_cost(WEIGHTED,(0,0),(4,4))==7
    assert r['tree']=={'minimax':5,'alpha_beta':5}
    expected = {'2':{'best_target':'T2','best_value':-1},'4':{'best_target':'T3','best_value':3}}
    for h,value in expected.items():
        assert r['treasure'][h]=={'minimax':value,'alpha_beta':value}
    labels=('A','B','T1','T2','T3','T4')
    matrix=[[0,12,10,4,8,8],[12,0,8,8,4,10],[10,8,0,6,6,12],
            [4,8,6,0,6,6],[8,4,6,6,0,6],[8,10,12,6,6,0]]
    pos={v:(i,j) for i,row in enumerate(TREASURE) for j,v in enumerate(row) if isinstance(v,str) and v!='X'}
    for i,a in enumerate(labels):
        for j,b in enumerate(labels):
            assert r['distance_matrix'][a][b]==matrix[i][j]==dijkstra_cost(TREASURE,pos[a],pos[b],free_goal=False)
    return {'status':'passed','maze_steps':7,'weighted_cost':7,'tree_value':5,'treasure':expected}


if __name__=='__main__':
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
