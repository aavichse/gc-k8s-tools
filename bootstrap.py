import argparse
from typing import Any
from pathlib import Path
from jinja2 import Environment , FileSystemLoader, Template
from dataclasses import asdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import yaml

# Args 
parser = argparse.ArgumentParser(description="Generate manifests for scale environment that simulate high volume traffic")
parser.add_argument('--config', type=str, default='config.yaml', help='configuration file (default=config.yaml)')
args = parser.parse_args()


@dataclass
class Context:
    bootstrap_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    namespaces: int = 1
    deployments: int = 1
    replicaset: int = 1

    stat_interval: int = 10
    total_connections: int = 100
    connection_per_interval: int = 10   # for a single pod
    batch_size: int = 5
    same_ns_ratio: int = 30    
    
    no_labels_per_pod: int = 5
    total_labels: int = 0

    it:  dict[str, int] = field(default_factory=dict)   

    @staticmethod
    def from_yaml(path: str) -> "Context":
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
        workloads = raw.get("workloads", {})
        context = Context(
            namespaces=int(workloads['namespaces']), 
            deployments=int(workloads['deployments']),
            replicaset=int(workloads['replicaset']),
            total_labels=int(workloads['total_labels']),
            stat_interval=int(raw['stat_interval']),
            total_connections=int(raw['total_connections']),
            batch_size=int(raw['batch_size']),
            same_ns_ratio=int(raw['same_ns_ratio']),
        )
        
        context.no_labels_per_pod = max(1,  int(context.total_labels / (context.namespaces * context.deployments)))
        context.connection_per_interval = int(context.total_connections / (
            context.namespaces * context.deployments * context.replicaset
        ))
        return context

env = Environment(
    loader=FileSystemLoader("."), 
    trim_blocks=True, 
    lstrip_blocks=True
)


ns_template = env.get_template('template.namespace.yaml')
deployment_template = env.get_template('template.deployment.yaml')

outdir: Path 

context: Context

def bootstrap_manifests(): 
    namespaces = context.namespaces
    deployments = context.deployments
    replica = context.replicaset
    print(f'Writes manifests for: {namespaces=}, {deployments=} ({replica=})')
    print(f'Total labels: {context.total_labels}, per-pod={context.no_labels_per_pod}')
    print(f'Total connections: {context.total_connections} per {context.stat_interval} seconds, per-pod={context.connection_per_interval} ')
    for i in range(1, context.namespaces+1): 
        context.it['i'] = i
        namespace = _write_namespace(index=i)    
        for j in range(1, context.deployments+1): 
            context.it['j'] = j
            _write_deployment(namespace=namespace, index=j)
    print(f'generated in: {outdir}, total workloads={namespaces*deployments*replica}')
            
    
def _write_namespace(index: int) -> str:
    namespace = f'gc-ns-{index}'
    rendered = ns_template.render(**asdict(context))
    ns_manifest_path = outdir / 'namespaces' / f'{namespace}.yaml'
    ns_manifest_path.write_text(rendered)
    return namespace 
    
    
def _write_deployment(namespace: str, index: int):
    deployment = f'{namespace}-rs-{index}'
    rendered = deployment_template.render(**asdict(context))
    ns_manifest_path = outdir / f'{deployment}.yaml'
    ns_manifest_path.write_text(rendered)

def render_values_template(path: str, number: int) -> Dict[str, Any]:
    """
    Replace '{{ NUMBER }}' in values.yaml with the given number,
    without evaluating the whole file as a Jinja2 template.
    """
    raw = Path(path).read_text()
    rendered = raw.replace("{{ NUMBER }}", str(number))
    return yaml.safe_load(rendered)


def gc_labels(indent: int, count: int) -> str: 
    i = context.it['i']
    j = context.it['j']
    labels: Dict[str, str] = {
        f'gc-label-{i}-{j}-idx{idx}': f'gc-value-{i}-{j}-idx{idx}'
        for idx in range(1, count + 1)
    }
    
    dumped = yaml.dump(labels, default_flow_style=False, sort_keys=True).rstrip()
    indented = '\n'.join(' ' * indent + line for line in dumped.splitlines())    
    return indented


def main():
    global context, outdir, env
    
    env.globals['gc_labels'] = gc_labels

    context = Context.from_yaml(args.config)

    outdir = Path('output', context.bootstrap_id)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir/'namespaces').mkdir()

    bootstrap_manifests()


if __name__ == '__main__': 
    main()