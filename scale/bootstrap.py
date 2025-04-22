from typing import Any
from pathlib import Path
from jinja2 import Environment , FileSystemLoader, Template
from dataclasses import asdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import yaml


@dataclass
class Context:
    bootstrap_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    namespaces: int = 1
    deployments: int = 1
    replicaset: int = 1

    stat_interval: int = 10
    connection_per_interval: int = 10
    batch_size: int = 5
    same_ns_ratio: int = 30    

    it:  dict[str, int] = field(default_factory=dict)   

    @staticmethod
    def from_yaml(path: str) -> "Context":
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
        workloads = raw.get("workloads", {})
        return Context(
            namespaces=int(workloads['namespaces']), 
            deployments=int(workloads['deployments']),
            replicaset=int(workloads['replicaset']),
            stat_interval=int(raw['stat_interval']),
            connection_per_interval=int(raw['connection_per_interval']),
            batch_size=int(raw['batch_size']),
            same_ns_ratio=int(raw['same_ns_ratio']),
        )

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
    for i in range(1, context.namespaces+1): 
        context.it['i'] = i
        namespace = _write_namespace(index=i)    
        for j in range(1, context.deployments+1): 
            context.it['j'] = j
            _write_deployment(namespace=namespace, index=j)
            

def _write_namespace(index: int) -> str:
    namespace = f'gc-ns-{index}'
    rendered = ns_template.render(**asdict(context))
    ns_manifest_path = outdir / 'namespaces' / f'{namespace}.yaml'
    ns_manifest_path.write_text(rendered)
    return namespace 
    
    
def _write_deployment(namespace: str, index: int):
    deployment = f'{namespace}-deployment-{index}'
    rendered = deployment_template.render(**asdict(context))
    ns_manifest_path = outdir / f'{deployment}.yaml'
    ns_manifest_path.write_text(rendered)



def main():
    global context, outdir
    
    context = Context.from_yaml('config.yaml')

    outdir = Path('output', context.bootstrap_id)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir/'namespaces').mkdir()

    bootstrap_manifests()


if __name__ == '__main__': 
    main()