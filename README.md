## Bootstrap strip 

**bootstrap.py** generates Kubernetes manifests for a scalable workload simulation environment, creating namespaces (`gc-ns-X`), deployments (`gc-ns-rs-Y`), and services with configurable parameters like namespace count, deployments, replicas, and traffic. 
It aims to simulate scalable workloads with high volume of labels and traffic. 

### configuration
```
outdir: output 

stat_interval: 10
total_connections: 100   # total connections per interval
same_ns_ratio: 30
batch_size: 5


workloads: 
  namespaces: 3
  deployments: 2
  replicaset: 1
  total_labels: 1000
```

The configuration defines parameters for generating Kubernetes namespaces (gc-ns-X), deployments (gc-ns-deployment-Y), and services to simulate high-volume traffic. It specifies:  

`output`: Manifests are written to the output directory, organized by a unique bootstrap ID.  
**Traffic Settings**:  
`stat_interval`: 10 sets a 10-second interval for connection statistics.  
`total_connections`: 100 targets 100 connections per 10-second interval.  
`same_ns_ratio`: 30 directs 30% of connections to the same namespace (next deployment) and 70% to the next namespace (same deployment).  
`batch_size`: 5 sends 5 concurrent requests per batch.  
**Workloads**:  
`namespaces`: 3 creates 3 namespaces (gc-ns-1 to gc-ns-3).  
`deployments`: 2 creates 2 deployments per namespace (gc-ns-deployment-1, gc-ns-deployment-2).  
`replicaset`: 1 sets 1 replica per deployment.  
`total_labels`: 1000 assigns 1000 labels across all pods, with approximately 1000 / (3 * 2) ≈ 167 labels per pod.  

### Usage
```bash
docker run -ti -v $(pwd):/app/config -v $(pwd)/output:/app/output arikab64/gc-wlsim:1.3 python bootstrap.py  --config /app/config/my-config.yaml
```

*note:  my-config.yaml mounted from local disk*
