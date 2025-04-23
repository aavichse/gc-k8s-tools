#!/bin/bash 

for ns in gc-ns-{1..5}; do
  kubectl get namespace $ns -o json | jq '.spec.finalizers = []' \
    | kubectl replace --raw "/api/v1/namespaces/$ns/finalize" -f -
done