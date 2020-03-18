# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 21:59:09 2020

@author: Giliard Almeida de Godoi
"""
from collections import deque

from graph import Graph
from util import gg_rooted_tree

class Chromossome():

    def __init__(self, subtree : Graph, start_node, fitness=0):
        self.subtree = subtree
        self.start_node = start_node
        self.fitness = fitness

class PartitionCrossover():

    def __init__(self, graph_data : Graph):
        self.graph = graph_data

    def crossover(self, parent_1 : Chromossome, parent_2 : Chromossome):

        subtree_1 = parent_1.subtree
        subtree_2 = parent_2.subtree

        # Primeiro uma das soluções será transformada na sua forma enraizada
        s1 = parent_1.start_node

        rooted_tree_1 = gg_rooted_tree(subtree_1, s1)

        disjoint_edges_2, GGsub2 = self.disjoints_edges_and_subgraph(subtree_1, subtree_2)


        # DETERMINAR AS PARTIÇÕES DE UM DOS PAIS E OS VÉRTICES COMUNICANTES

        subsets = list()

        while disjoint_edges_2 :
            v, u = disjoint_edges_2.pop()

            # poderia ter sido
            ## if subtree_1.has_node(v) and subtree_1.has_node(u):
            if (v in rooted_tree_1) and (u in rooted_tree_1):
                tmp = {
                    'edges' : {(v , u)},
                    'common' : [v, u],
                    'cost' : self.graph.weight(v, u)
                }
                subsets.append(tmp)

            elif (v in rooted_tree_1) and (not u in rooted_tree_1):
                tmp = self.DFS_with_stop(rooted_tree_1, disjoint_edges_2, GGsub2, u)
                subsets.append(tmp)

            elif not (v in rooted_tree_1) and (u in rooted_tree_1):
                # print('v ', v)
                tmp = self.DFS_with_stop(rooted_tree_1, disjoint_edges_2, GGsub2, v)
                subsets.append(tmp)

            else :
                tmp = self.DFS_with_stop(rooted_tree_1, disjoint_edges_2, GGsub2, v)
                subsets.append(tmp)


        partitions = dict()
        counter = 0

        for ss in subsets :
            assert len(ss['common']) >= 2, 'Vertices em comun deve ser maior ou igual a 2'
            v = ss['common'][0]
            subsets_2 = {'edges' : set(),'common' : [v], 'cost' : 0}
            for u in ss['common'][1:] :
                edges, cost = self.find_uncommon_edges_from_path(rooted_tree_1, v, u, subtree_2)
                subsets_2['edges'].update(edges)
                subsets_2['common'].append(u)
                subsets_2['cost'] += cost

            partitions[counter] = {'sub1' : ss, 'sub2' : subsets_2 }
            counter += 1

        # REALIZAR A COMPARAÇÃO E MONTAR A SOLUÇÃO FINAL
        GG_child = Graph()
        cost_child = 0

        for v, u in subtree_1.gen_undirect_edges():
            if subtree_2.has_edge(v, u):
                ww = self.graph.weight(v, u)
                cost_child += ww
                GG_child.add_edge(v, u, weight= ww)

        for _, pp in partitions.items():
            edges = {}

            if pp['sub1']['cost'] <= pp['sub2']['cost'] :
                edges = pp['sub1']['edges']
                # print('sub1 escolhido')

            elif pp['sub2']['cost'] < pp['sub1']['cost'] :
                edges = pp['sub2']['edges']
                # print('sub2 escolhido')


            for v , u in edges:
                ww = self.graph.weight(v, u)
                cost_child += ww
                GG_child.add_edge(v, u, weight= ww)
                
        
        return Chromossome(GG_child, s1, cost_child)


    def std_edges(self, x, y):
        '''
        Uma função auxiliar para padronizar as arestas. Será necessário?
        '''
        return (min(x,y), max(x,y))


    def disjoints_edges_and_subgraph(self, subtree_1 : Graph, subtree_2 : Graph):

        # Definir o conjunto de arestas que somente pertence a subtree_2
        disjoint_edges_2 = set()

        # componentes desconexas de subtree_2
        # esse grafo sera usado por DFS_with_stop para identificar de maneira mais
        # direta, os extremos (vértices comuns) de uma partição de arestas não comuns
        # do pai 2
        GGsub2 = Graph()

        # determinando somente as arestas não comum do pai 2
        for v, u in subtree_2.gen_undirect_edges():
            if not subtree_1.has_edge(v, u):
                GGsub2.add_edge(v, u)
                disjoint_edges_2.add(self.std_edges(v, u))

        return disjoint_edges_2, GGsub2


    def DFS_with_stop(self, rooted_tree_1 : dict, disjoint_edges_2 : set, GGsub2 : Graph, start):

        stack = deque()
        stack.append(start)

        visited = set([start])
        # previous = { start : None }
        previous = set()
        cost = 0

        common_vertice = list()

        while stack :
            v = stack.pop()
            visited.add(v)

            for u in GGsub2.adjacent_to(v):
                if (not u in visited) and (not u in rooted_tree_1):
                    stack.append(u)
                elif u in rooted_tree_1:
                    common_vertice.append(u)

                previous.add(self.std_edges(v, u))
                cost += self.graph.weight(v,u)

                disjoint_edges_2.discard(self.std_edges(v, u))

        partition = {
            'edges' : previous,
            'common' : common_vertice,
            'cost' : cost
                }

        return partition


    def find_uncommon_edges_from_path(self, rtree, a, b, subtree):
        edges = set()
        cost = 0

        v = a
        while rtree[v] :
            previous = rtree[v]

            if not subtree.has_edge(v, previous):
                edges.add(self.std_edges(v, previous))
                w = self.graph.weight(v, previous)
                # print(f"Verificar aresta ({v}, {previous}) - Peso  {w}")
                cost += w

            v = rtree[v]

        u = b
        while rtree[u]:
            previous = rtree[u]

            if not subtree.has_edge(u, previous):
                edges.add(self.std_edges(u, previous))
                w = self.graph.weight(u, previous)
                # print(f"Verificar aresta ({u}, {previous}) - Peso  {w}")
                cost += w

            u = rtree[u]


        return edges, cost


    def common_graph(self, subtree_1 : Graph, subtree_2 : Graph):

        GG_child = Graph()

        for v, u in subtree_1.gen_undirect_edges():
            if subtree_2.has_edge(v, u):
                ww = self.graph.weight(v, u)
                GG_child.add_edge(v, u, weight= ww)

        return GG_child

if __name__ == "__main__":
    import random
    from os import path
    from graph import Reader
    from graph.steiner_heuristics import shortest_path_with_origin

    arquivo = path.join("datasets","b13.stp")

    reader = Reader()

    stp = reader.parser(arquivo)

    graph = Graph(vertices=stp.nro_nodes, edges=stp.graph)

    ## DETERMINAR DUAS SOLUÇÕES PARCIAIS PELAS HEURISTICAS

    # escolher aleatoriamente um vértice terminal
    s1 = random.choice(stp.terminals)
    subtree_1, cost1 = shortest_path_with_origin(graph, s1, stp.terminals) # 0 ate 16

    s2 = random.choice(stp.terminals)
    subtree_2, cost2 = shortest_path_with_origin(graph, s2, stp.terminals)
    
    parent_1 = Chromossome(subtree_1, s1, cost1)
    parent_2 = Chromossome(subtree_2, s2, cost2)
    
    PX = PartitionCrossover(graph)
    
    child = PX.crossover(parent_1, parent_2)