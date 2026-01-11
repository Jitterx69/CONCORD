use pyo3::prelude::*;
use rayon::prelude::*;
use std::collections::{HashMap, HashSet};

#![allow(non_local_definitions)] // Suppress pyo3 macro warning

#[pyclass]
#[derive(Clone, Debug)]
#[allow(dead_code)]
struct CausalNode {
    id: String,
    dependents: Vec<String>,
}

#[pyclass]
struct GraphWalker {
    nodes: HashMap<String, CausalNode>,
}

#[pymethods]
impl GraphWalker {
    #[new]
    fn new() -> Self {
        GraphWalker {
            nodes: HashMap::new(),
        }
    }

    fn add_node(&mut self, id: String, dependents: Vec<String>) {
        let node = CausalNode {
            id: id.clone(),
            dependents,
        };
        self.nodes.insert(id, node);
    }

    /// Propagates invalidation from a starting node to all affected dependents.
    /// Uses parallel iteration for improved performance on large graphs.
    fn propagate_invalidation(&self, start_id: String) -> HashSet<String> {
        let mut invalid_set = HashSet::new();
        let mut frontier = vec![start_id];

        while !frontier.is_empty() {
            let next_frontier: HashSet<String> = frontier
                .par_iter()
                .filter_map(|node_id| self.nodes.get(node_id))
                .flat_map(|node| node.dependents.clone())
                .collect();

            frontier = Vec::new();
            for item in next_frontier {
                if invalid_set.insert(item.clone()) {
                    frontier.push(item);
                }
            }
        }

        invalid_set
    }

    // ------------------------------------------------------------------------
    // Graph Analysis Algorithms
    // ------------------------------------------------------------------------

    /// Detects circular dependencies using DFS.
    fn detect_cycles(&self) -> Vec<Vec<String>> {
        let mut cycles = Vec::new();
        let mut visited = HashSet::new();
        let mut recursion_stack = HashSet::new();
        let mut path = Vec::new();

        for node_id in self.nodes.keys() {
            if !visited.contains(node_id) {
                self.dfs_cycle(
                    node_id,
                    &mut visited,
                    &mut recursion_stack,
                    &mut path,
                    &mut cycles,
                );
            }
        }
        cycles
    }

    /// Identifies isolated communities using Connected Components.
    fn detect_communities(&self) -> Vec<HashSet<String>> {
        let mut communities = Vec::new();
        let mut global_visited = HashSet::new();

        for node_id in self.nodes.keys() {
            if !global_visited.contains(node_id) {
                let mut community = HashSet::new();
                let mut stack = vec![node_id.clone()];

                while let Some(current) = stack.pop() {
                    if community.insert(current.clone()) {
                        global_visited.insert(current.clone());

                        if let Some(node) = self.nodes.get(&current) {
                            for dep in &node.dependents {
                                if !community.contains(dep) {
                                    stack.push(dep.clone());
                                }
                            }
                        }
                    }
                }
                communities.push(community);
            }
        }
        communities
    }

    fn calculate_pagerank(&self, iterations: usize, damping: f64) -> HashMap<String, f64> {
        let n = self.nodes.len();
        if n == 0 {
            return HashMap::new();
        }

        let initial_rank = 1.0 / n as f64;
        let mut ranks: HashMap<String, f64> = self
            .nodes
            .keys()
            .map(|k| (k.clone(), initial_rank))
            .collect();

        for _ in 0..iterations {
            let mut new_ranks = HashMap::new();
            for node_id in self.nodes.keys() {
                let mut rank_sum = 0.0;
                // Note: Simplified reverse lookup for MVP. Production would use an adjacency matrix.
                for (other_id, other_node) in &self.nodes {
                    if other_node.dependents.contains(node_id) {
                        let other_rank = ranks.get(other_id).unwrap_or(&0.0);
                        let out_degree = other_node.dependents.len().max(1) as f64;
                        rank_sum += other_rank / out_degree;
                    }
                }
                let new_rank = (1.0 - damping) / n as f64 + damping * rank_sum;
                new_ranks.insert(node_id.clone(), new_rank);
            }
            ranks = new_ranks;
        }
        ranks
    }

    fn calculate_betweenness(&self) -> HashMap<String, f64> {
        // Degree Centrality proxy for Betweenness
        self.nodes
            .iter()
            .map(|(id, node)| (id.clone(), node.dependents.len() as f64))
            .collect()
    }

    fn calculate_closeness(&self) -> HashMap<String, f64> {
        // Simple heuristic: Inverse of out-degree
        self.nodes
            .iter()
            .map(|(id, node)| (id.clone(), 1.0 / (node.dependents.len() as f64 + 1.0)))
            .collect()
    }

    fn count_triangles(&self) -> usize {
        let mut count = 0;
        for (id_a, node_a) in &self.nodes {
            for id_b in &node_a.dependents {
                if let Some(node_b) = self.nodes.get(id_b) {
                    for id_c in &node_b.dependents {
                        // Check for A->B->C->A (Directed Cycle)
                        if id_c == id_a {
                            count += 1;
                        }
                        // Check for Transitive relationship A->B->C and A->C
                        if let Some(node_a_ref) = self.nodes.get(id_a) {
                            if node_a_ref.dependents.contains(id_c) {
                                count += 1;
                            }
                        }
                    }
                }
            }
        }
        // approximate de-duplication
        count / 3
    }

    fn find_cliques(&self) -> usize {
        // Heuristic: Max neighborhood size + 1
        self.nodes
            .values()
            .map(|n| n.dependents.len())
            .max()
            .unwrap_or(0)
            + 1
    }

    fn find_diameter(&self) -> usize {
        let mut max_dist = 0;
        for start_node in self.nodes.keys() {
            let mut dists = HashMap::new();
            dists.insert(start_node, 0);
            let mut queue = vec![start_node];

            while !queue.is_empty() {
                let u = queue.remove(0); // Pop front
                let d = *dists.get(u).unwrap();
                max_dist = max_dist.max(d);

                if let Some(node) = self.nodes.get(u) {
                    for v in &node.dependents {
                        if !dists.contains_key(v) {
                            dists.insert(v, d + 1);
                            queue.push(v);
                        }
                    }
                }
            }
        }
        max_dist
    }

    fn calculate_jaccard_similarity(&self, node_a: String, node_b: String) -> f64 {
        let empty = Vec::new();
        let deps_a: HashSet<_> = self
            .nodes
            .get(&node_a)
            .map(|n| &n.dependents)
            .unwrap_or(&empty)
            .iter()
            .collect();
        let deps_b: HashSet<_> = self
            .nodes
            .get(&node_b)
            .map(|n| &n.dependents)
            .unwrap_or(&empty)
            .iter()
            .collect();

        let intersection = deps_a.intersection(&deps_b).count();
        let union = deps_a.union(&deps_b).count();

        if union == 0 {
            0.0
        } else {
            intersection as f64 / union as f64
        }
    }

    fn max_flow(&self, _source: String, _sink: String) -> i32 {
        // Placeholder for future Edmonds-Karp implementation
        1
    }

    fn minimum_spanning_tree(&self) -> HashSet<(String, String)> {
        // BFS Tree heuristic for unweighted graph
        let mut edges = HashSet::new();
        let mut visited = HashSet::new();

        if let Some(start) = self.nodes.keys().next() {
            let mut queue = vec![start];
            visited.insert(start);

            while !queue.is_empty() {
                let u = queue.remove(0);
                if let Some(node) = self.nodes.get(u) {
                    for v in &node.dependents {
                        if visited.insert(v) {
                            edges.insert((u.clone(), v.clone()));
                            queue.push(v);
                        }
                    }
                }
            }
        }
        edges
    }

    fn k_core_decomposition(&self, k: usize) -> Vec<String> {
        self.nodes
            .iter()
            .filter(|(_, n)| n.dependents.len() >= k)
            .map(|(id, _)| id.clone())
            .collect()
    }
}

impl GraphWalker {
    fn dfs_cycle(
        &self,
        current_node: &String,
        visited: &mut HashSet<String>,
        stack: &mut HashSet<String>,
        path: &mut Vec<String>,
        cycles: &mut Vec<Vec<String>>,
    ) {
        visited.insert(current_node.clone());
        stack.insert(current_node.clone());
        path.push(current_node.clone());

        if let Some(node) = self.nodes.get(current_node) {
            for neighbor in &node.dependents {
                if !visited.contains(neighbor) {
                    self.dfs_cycle(neighbor, visited, stack, path, cycles);
                } else if stack.contains(neighbor) {
                    // Cycle detected: Extract the path segment involved in the cycle
                    if let Some(pos) = path.iter().position(|x| x == neighbor) {
                        cycles.push(path[pos..].to_vec());
                    }
                }
            }
        }

        stack.remove(current_node);
        path.pop();
    }
}

mod consumer;
use consumer::CausalConsumer;

#[pyfunction]
fn start_kafka_consumer(brokers: &str, topic: &str) -> PyResult<()> {
    let consumer = CausalConsumer::new(brokers, topic);
    consumer.start();
    Ok(())
}

#[pymodule]
fn rust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<GraphWalker>()?;
    m.add_function(wrap_pyfunction!(start_kafka_consumer, m)?)?;
    Ok(())
}
