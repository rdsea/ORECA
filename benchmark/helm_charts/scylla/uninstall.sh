#!/bin/bash
helm uninstall scylla -n scylla
helm uninstall scylla-manager -n scylla-manager
helm uninstall scylla-operator -n scylla-operator
