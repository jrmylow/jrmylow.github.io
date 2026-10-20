---
layout: page
title: Projects
permalink: /projects/
nav_order: 40
---

A collection of personal projects and highlights from my time at Georgia Tech's OMSCS program (systems track).

## Distributed Systems and Fault Tolerance

{% include details_open.html title="MapReduce Implementation with Master Failover" summary="MapReduce implementation in Go for distributed data processing, incorporating replication and failover for Master nodes" %}

Coursework implementations of MapReduce, such as in MIT's 6.824/6.5840, typically assume that the Master node is reliable. This project extends that by deliberately crashing the Master and workers, requiring a level of replication from an active Master (Leader) node to backup Master nodes to avoid losing work in long-running batch computations.

* **Context**: written in Go in a team of 2, deployed on Azure Kubernetes Service, using Azure Blob Storage as the distributed file system. I owned the design of the Master and Worker fault tolerance.
* **Verification**: reconciliation vs. reference implementation, randomised fault injection (crashes) for Master and Worker nodes

Key design decisions:

* **Leader election and failover**: Used etcd as a backing service to manage Leader identity between Master nodes through election on a shared key.
* **Atomic job-state updates**: Ensured that internal data structures for each job are updated only on successful job completion, minimising complexity in tracking WIP state across workers. Only a coherent job state would ever be propagated towards backup Master nodes.
* **Idempotent job advancement**: Simplified the job-processing code to accept any job (new, in-progress, or complete) and advance it towards completion.

Job state is broadcast from Leader to backup, with version numbers per-job to ensure forward progress is maintained. Upon Leader failure, a backup can step up by acquiring a lease on the shared key. Because backups only receive coherent state updates, they can call the handler to advance the computation directly. The net impact is clean failover and minimal reliance on etcd for coordination, minimising the risk that service becomes a performance bottleneck.

{% include details_close.html %}

## Personal Projects

{% include details_open.html title="Website Testing Infrastructure" summary="Containerised development and test environment for the site, with public write-up available [here](/2026/06/20/building)." %}

* **Context**: sandbox for AI-augmented development experiments, protecting data from untrusted code
* **Verification**: automated regression suite with playwright and pytest, integrated with GitHub CI, with manual verification of major changes
* **Availability**: at [github](https://github.com/jrmylow/jrmylow.github.io)

Key design decisions:

* **Threat model**: data exfiltration is bounded through keeping secrets and sensitive information away from the test environment. The container serves to provide reasonable protection from agent-generated test code to the host and filesystem through rootless containers.
* **Reproducibility**: dependencies are pinned to match GitHub Pages workflow and ensure Playwright testing matches the end-user experience

{% include details_close.html %}

## Systems Programming

{% include details_open.html title="Cache-Oblivious Sort Implementation" summary="Implementation and theoretical analysis (write-up [here](/2026/10/05/funnelsort)) of Funnelsort algorithm and impact of simplified memory layout for the recursive van Emde Boas tree structure on asymptotic efficiency." %}

* **Context**: written in C, with memory safety by construction due to the exact layout of the data buffer layouts
* **Verification**: data reconciliation tests, checks with valgrind, cache-miss performance measured with cachegrind (66% cache miss reduction compared to naive mergesort)

{% include details_close.html %}

{% include details_open.html title="File Cache Server via IPC" summary="File cache service that provides a backing store for a proxy server, using shared memory IPC to provide file data to multiple concurrent processes." %}

The file cache server provides an abstraction over the underlying file system, mitigating risk of file descriptor exhaustion, disk I/O management, and buffering content to lower latency for frequently-accessed files.

* **Context**: written in C, using POSIX shared memory and message queue primitives, and cache invalidation out of scope
* **Verification**: integration test suite, checks with valgrind/helgrind

{% include details_close.html %}

{% include details_open.html title="SampleSort Implementation" summary="Implementation of parallel sorting with regular sampling (PSRS) algorithm, for distributed sorting of large data sets." %}

* **Context**: written in C using MPI, with highly skewed keys de-scoped
* **Verification**: data reconciliation tests, checks with valgrind, sort performance measured by wall-clock on cluster (0.23s for 1.6GB data, distributed over 4 nodes and 64 processes)

{% include details_close.html %}

## Networking and Cloud

{% include details_open.html title="Software-Defined Networking and Network Virtualisation" summary="Network routing, provisioning, connection management, and testing for virtualised network services over a software-defined network." %}

Implementation of multiple OpenFlow controllers to demonstrate network routing protocol algorithms (shortest path, widest path, and load-balancing) and virtual network function management over a software-defined network.

* **Context**: written in Python in a team of 2, using OpenFlow and k8s-deployed network functions. I designed the test suite, controller handling of network faults, and connection affinity for virtual network functions.
* **Verification**: live connectivity and load generation using `iperf3` and a custom testing framework, network rebalancing and connection affinity demonstrated through logs

Key design decisions:

* **Test Suite**: designed test suite to generate and run network tests, with support for time-varying workload and network fault injection
* **Network-fault tolerance**: included handling for network topology changes and link uptime/downtime
* **Adaptive algorithms**: extended widest-path controller to include network telemetry when redistributing network flows
* **Connection affinity**: implemented connection affinity management for stateful services e.g. NAT, ensuring both outbound and inbound connections are correctly routed between nodes

{% include details_close.html %}

{% include details_open.html title="Cloud Application Infrastructure" summary="Infrastructure provisioning and configuration for a cloud-native microservices app" %}

* **Context**: written in a team of 2, using go and Terraform. I owned the infrastructure provisioning design.
* **Verification**: local testing environment (kind, azurite), then deployed to Azure managed services, with infrastructure changes verified through integration tests

Key design decisions:

* **Compute provisioning**: allocation of application layers across cloud offerings, with stateful services on managed k8s and the stateless customer-facing endpoints on Azure App Service with autoscaling
* **Security**: moved application to isolated network connections using virtual network, to minimise exposure to public internet

{% include details_close.html %}
