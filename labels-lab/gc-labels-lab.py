#!/usr/bin/env python3

import argparse
import yaml
import time
import os
import random
import string


DEFAULT_LABEL_VALUE_LENGTH = 63


total_workloads = 0
total_labels = 0


def render_yaml(template: str, context: dict) -> str:
    """
    Render a template string by replacing placeholders with context values.

    Args:
        template (str): The template string containing placeholders.
        context (dict): A dictionary with keys matching placeholders in the template.

    Returns:
        str: The rendered string with placeholders replaced by context values.
    """
    return template.format(**context)


def format_labels_as_indented_yaml(labels: dict, indent: int = 4) -> str:
    """
    Format a dictionary of labels into an indented YAML-like string.

    Args:
        labels (dict): A dictionary of key-value pairs to be formatted.
        indent (int): The number of spaces for indentation.

    Returns:
        str: A formatted string representing the labels.
    """
    indentation = ' ' * indent
    label_lines = [
        f'{indentation}{labelName}: "{labelValue}"'
        for labelName, labelValue in labels.items()
    ]
    return "\n".join(label_lines)


def generate_label_value(length: int) -> str:
    """
    Generate a random alphanumeric string of the specified length.

    Args:
        length (int): The desired length of the random string.

    Returns:
        str: A random string of the specified length.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_labels(
    namespace: str,
    workload_type: str,
    deployment_name: str,
    label_patterns: dict,
    context: dict,
    prefix: str = '',
    context_key_prefix: str = 'Labels',
) -> int:
    """
    Generate labels or annotations and add them to the context for rendering.

    Args:
        deployment_name (str): The name of the deployment to use in the labels.
        label_patterns (dict): A dictionary specifying label patterns and their configurations.
        context (dict): A dictionary to update with generated labels or annotations.
        prefix (str): A prefix to add to each label key (e.g., 'annotation-' for annotations).
        context_key_prefix (str): The prefix for keys in the context (e.g., 'Labels', 'Annotations').

    Updates:
        context: Adds formatted labels or annotations to the context.

    Returns:
        Number of labels
    """
    labels = {}
    for pattern, options in label_patterns.items():
        count = options.get('count', 1)
        value_length = options.get('length', DEFAULT_LABEL_VALUE_LENGTH)
        for i in range(1, count + 1):
            label_key = prefix + f'{pattern}-{i}'.format(
                namespace=namespace,
                deployment_name=deployment_name,
                workload_type=workload_type,
                index=i,
            )
            labels[label_key] = generate_label_value(value_length)

    for indent in [4, 6, 8]:
        context[f'{context_key_prefix}_{indent}'] = format_labels_as_indented_yaml(
            labels, indent
        )

    return len(labels)


def fill_labels_namespace(ns_config: dict, template_path: str, outdir: str, context):
    global total_labels

    context['Namespace'] = ns_config.get('name')

    ns_template_path = os.path.join(template_path, 'namespace.yaml')
    with open(ns_template_path, 'r') as fp:
        ns_template = fp.read()

    ns_name = ns_config.get('name', 'default')
    label_patterns = ns_config.get('label_patterns', {})

    labels_count = generate_labels(
        namespace=ns_name,
        workload_type='namespace',
        deployment_name=ns_name,
        label_patterns=label_patterns,
        context=context,
    )
    generate_labels(
        namespace=ns_name,
        workload_type='namespace',
        deployment_name=ns_name,
        label_patterns=label_patterns,
        context=context,
        prefix='annotation-',
        context_key_prefix="Annotations",
    )

    rendered_ns_yaml = render_yaml(ns_template, context)

    namespace_yaml_path = os.path.join(outdir, 'namespace.yaml')
    with open(namespace_yaml_path, 'w') as fp:
        fp.write(rendered_ns_yaml)

    total_labels += labels_count


def fill_labels_workloads(
    namespace: str, workloads: dict, template_path: str, outdir: str, context
):
    """
    Generate Kubernetes YAML resources for scaling workloads based on configuration.

    Args:
        config (dict): Configuration specifying namespace, workloads, and label patterns.
        template_path (str): Path to the directory containing YAML templates.
        outdir (str): Path to the directory where output files will be written.

    Raises:
        ValueError: If the namespace is missing from the configuration.

    Creates:
        YAML files for the namespace and workloads in the specified output directory.
    """
    global total_workloads
    global total_labels

    for workload_type, workload_config in workloads.items():
        count = workload_config.get('count', 1)
        label_patterns = workload_config.get('label_patterns', {})

        print(f'Generating {workload_type=}, {count=}')
        template_file = os.path.join(template_path, f'{workload_type}.yaml')
        if not os.path.exists(template_file):
            print(
                f'Warning: Template for {workload_type} not found at {template_path}. skipping'
            )
            continue

        workload_dir = os.path.join(outdir, workload_type)
        os.makedirs(workload_dir, exist_ok=True)

        with open(template_file, 'r') as wf:
            workload_template = wf.read()

        for i in range(1, count + 1):
            context['Id'] = i

            labels_count = generate_labels(
                namespace=namespace,
                workload_type=workload_type,
                deployment_name=f'{workload_type}-{i}',
                label_patterns=label_patterns,
                context=context,
            )

            generate_labels(
                namespace=namespace,
                workload_type=workload_type,
                deployment_name=f'{workload_type}-{i}',
                label_patterns=label_patterns,
                context=context,
                prefix="annotation-",
                context_key_prefix="Annotations",
            )

            rendered_workload_yaml = render_yaml(workload_template, context)

            workload_yaml_path = os.path.join(workload_dir, f'{workload_type}-{i}.yaml')
            with open(workload_yaml_path, 'w') as wf:
                wf.write(rendered_workload_yaml)

            total_workloads += 1
            total_labels += labels_count


def generate_config(total_labels, max_labels_per_workload):
    max_namespace_labels = 10
    namespace_label_count = min(total_labels, max_namespace_labels)
    total_labels -= namespace_label_count

    config = {
        "namespace": {
            "name": "gc-labels-lab",
            "label_patterns": {
                "gc-label-{namespace}-{deployment_name}": {
                    "count": namespace_label_count // 2,
                    "length": DEFAULT_LABEL_VALUE_LENGTH,
                },
                "gc-label-{namespace}-{deployment_name}-hash": {
                    "count": namespace_label_count // 2,
                    "length": DEFAULT_LABEL_VALUE_LENGTH,
                },
            },
        },
        "workloads": {},
    }

    workload_types = ["replicaset", "deployment", "cron"]
    workload_count = max(
        1, total_labels // (max_labels_per_workload * len(workload_types))
    )
    workload_labels = min(max_labels_per_workload, total_labels // workload_count)

    for workload_type in workload_types:
        config["workloads"][workload_type] = {
            "count": workload_count,
            "label_patterns": {
                "gc-label-{namespace}-{deployment_name}": {
                    "count": workload_labels // 2,
                    "length": DEFAULT_LABEL_VALUE_LENGTH,
                },
                "gc-label-{namespace}-{deployment_name}-hash": {
                    "count": workload_labels // 2,
                    "length": DEFAULT_LABEL_VALUE_LENGTH,
                },
            },
        }

    return config


def main():
    parser = argparse.ArgumentParser(
        description='Generating Deployment with numerous labels and workloads'
    )
    parser.add_argument('-f', '--config', help='Path to plan scale generator')
    parser.add_argument(
        '-t', '--template', default='./templates', help='Path to template Yamls'
    )
    parser.add_argument(
        '--generate-config',
        action='store_true',
        help='Generate a configuration based on total labels',
    )
    parser.add_argument(
        '--total-labels',
        type=int,
        default=100,
        help='Total number of labels to generate',
    )
    parser.add_argument(
        '--max-labels-per-workload',
        type=int,
        default=50,
        help='Maximum labels per workload',
    )
    parser.add_argument(
        '--out',
        type=str,
        default='generated-config.yaml',
        help='Output of generated config file',
    )

    args = parser.parse_args()

    if args.generate_config:
        config = generate_config(args.total_labels, args.max_labels_per_workload)
        with open(args.out, 'w') as f:
            yaml.dump(config, f)
        print(f'Generated configuration saved to "{args.out}"')
        return

    with open(args.config, 'r') as config_file:
        config = yaml.safe_load(config_file)

    context = {}
    ns_config = config.get('namespace', {})
    namespace = ns_config.get('name')

    outdir = os.path.join('output', f'{namespace}_{time.strftime("%Y%m%d-%H%M%S")}')
    os.makedirs(outdir, exist_ok=True)

    fill_labels_namespace(
        ns_config=ns_config,
        template_path=args.template,
        outdir=outdir,
        context=context,
    )

    fill_labels_workloads(
        namespace=namespace,
        workloads=config.get('workloads', {}),
        template_path=args.template,
        outdir=outdir,
        context=context,
    )

    print(f'Totals: {total_workloads=}, {total_labels=}')


if __name__ == '__main__':
    main()
