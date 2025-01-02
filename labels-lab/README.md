<div align="center">
<p><a href="../README.md">← Back to gc-k8s-tools</a></p>
</div>



# Kubernetes Workload Label Generator
A tool to generate Kubernetes YAML manifests with configurable labels and annotations for testing orchestration scale and performance under high label loads.

## Features

- Generates namespace and workload (ReplicaSet, Deployment, CronJob) manifests
- Configurable label/annotation patterns and counts
- Custom label value lengths
- Auto-generates configuration based on total desired labels
- Template-based manifest generation


## Generating Environment 

The `-f` flag allows generating Kubernetes manifests using a YAML configuration file that defines:

- Namespace details and label patterns
- Workload types (ReplicaSet, Deployment, CronJob)
- Number of instances per workload
- Label patterns and counts per resource

Example:

```bash
./gc-labels-lab.py -f config.yaml
```

Sample configuration:
```yaml
namespace:
  name: scale-test-ns
  label_patterns:
    gc-label-{namespace}-{deployment_name}:
      count: 20  # Generates 20 labels
      length: 63 # Each label value is 63 chars

workloads:
  deployment:
    count: 5    # Creates 5 deployments
    label_patterns:
      gc-label-{namespace}-{deployment_name}:
        count: 30    # Generates 30 unique labels from this pattern to each Deployment 
        length: 20   # Each label value is 20 chars
      gc-label-{namespace}-{deployment_name}-hash:
        count: 20    # Generates 20 unique labels from this pattern for each Deployment 
        length: 10   # Each label value is 10 chars
```

Generated files are saved in `output/<namespace>_<timestamp>/`.

## Configuration File Structure
The YAML configuration allows custom label patterns using placeholders:

### Placeholders
- `{namespace}`: Namespace name (e.g., "scale-test-ns")
- `{deployment_name}`: Workload type with index (e.g., "cron-1", "deployment-3") 

### Example Configuration
```yaml
namespace:
 name: scale-test-ns
 label_patterns:
   gc-label-{namespace}-{deployment_name}:  # Becomes: gc-label-scale-test-ns-cron-1
     count: 20   # Generates 20 labels
     length: 63  # Each label value is 63 chars
   custom-{namespace}-test:                 # Custom pattern
     count: 10
   monitoring-{deployment_name}:            # Additional pattern
     count: 5

workloads:
 deployment:
   count: 5     # Creates 5 deployments
   label_patterns:
     app-{namespace}-{deployment_name}:     # Becomes: app-scale-test-ns-deployment-1
       count: 30
```

Each pattern generates unique labels with random values. Multiple patterns can be added to both namespace and workload sections.

## Generating Configuration
The --generate-config flag creates a configuration file with specified label counts:
```bash
./gc-labels-lab.py --generate-config \
  --total-labels 100 \                  # Total desired labels
  --max-labels-per-workload 50 \        # Max labels per resource (Default=100 per workload)
  --out config.yaml                     # Output config file  (Default="generated_config.yaml")
```

The generator creates a balanced configuration, distributing labels across namespace (up to 10 labels) and workloads while respecting the maximum labels per workload limit.

Example generation for 100 total labels with 50 max per workload:
```yaml
namespace:
  name: gc-labels-lab
  label_patterns:    # 10 namespace labels
    gc-label-{namespace}-{deployment_name}:
      count: 5
    gc-label-{namespace}-{deployment_name}-hash:
      count: 5

workloads:          # 90 remaining labels split across workloads
  deployment:
    count: 2        # Each workload gets 45 labels
    label_patterns:
      gc-label-{namespace}-{deployment_name}:
        count: 20
      gc-label-{namespace}-{deployment_name}-hash:
        count: 25
```

## Running With Docker 

Generate config on local directory : 
```bash
docker run -v $(pwd):/tmp/ \
  ghcr.io/aavichse/gc-labels-lab:1.0 --generate-config --total-labels 500 \
  --out /tmp/generated-config.yaml
```

Generate manifests from local config file: 
```bash
docker run -v $(pwd)/output:/app/output \
           -v $(pwd)/generated-config.yaml:/app/config.yaml \
  ghcr.io/aavichse/gc-labels-lab:1.0 -f /app/config.yaml 
```