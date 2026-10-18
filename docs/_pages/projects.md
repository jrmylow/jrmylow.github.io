---
layout: page
title: Projects
permalink: /projects/
nav_order: 40
---

A small collection of projects. Learning systems through building and breaking them. Click through for more detail behind each project.

## Distributed Systems and Fault Tolerance

{% include details_open.html title="MapReduce Implementation with Master-Fault Tolerance" summary="MapReduce implementation in Go for distributed data processing, incorporating replication and failover for Master nodes. I owned the design of the Master and Worker fault tolerance." %}

* **Context**: coursework project (pair programming), in Go, deployed on Azure Kubernetes Service, using Azure Blob Storage as the distributed file system
* **Verification**: reconciliation vs. reference implementation, randomised fault injection (crashes) for Master and Worker nodes
* **Availability**: private repository, code available on request

Coursework implementations of MapReduce, such as in MIT's 6.824/6.5840, typically assume that the Master node is reliable. This project extends that by deliberately crashing the Master and workers, requiring a level of replication from an active Master (Leader) node to backup Master nodes to avoid losing work in long-running batch computations.

Key design decisions:

* **Leader election and failover**: Used etcd as a backing service to manage Leader identity between Master nodes through election on a shared key.
* **Atomic job-state updates**: Ensured that internal data structures for each job are updated only on successful job completion, minimising complexity in tracking WIP state across workers. Only a coherent job state would ever be propagated towards backup Master nodes.
* **Idempotent job advancement**: Simplified the job-processing code to accept any job (new, in-progress, or complete) and advance it towards completion.

Job state is broadcast from Leader to backup, with version numbers per-job to ensure forward progress is maintained. Upon Leader failure, a backup can step up by acquiring a lease on the shared key. Because backups only receive coherent state updates, they can call the handler to advance the computation directly. The net impact is clean failover and minimal reliance on etcd for coordination, minimising the risk that service becomes a performance bottleneck.

{% include details_close.html %}

## Networking and Cloud

{% include details_open.html title="Software-Defined Networking and Network Virtualisation" summary="Network routing, provisioning, and connection management for virtualised network services over a software-defined network. I designed the test suite, controller handling of network faults, and connection affinity for virtual network functions." %}

* **Context**: coursework project (pair programming), in Python, using OpenFlow and k8s-deployed network functions in kind
* **Verification**: live connectivity and load generation using `iperf3` and a custom testing framework, network rebalancing and connection affinity demonstrated through logs
* **Availability**: private repository, code available on request

Coursework implementation of multiple OpenFlow controllers to demonstrate network routing protocols and network function management over a software-defined network.

Key design decisions:

* **Test Suite**: designed test suite to generate and run network tests, with support for time-varying workload and network fault injection
* **Network-fault tolerance**: included handling for network topology changes and link uptime/downtime
* **Adaptive algorithms**: extended widest-path controller to include network telemetry when redistributing network flows
* **Connection affinity**: implemented connection affinity management for stateful services e.g. NAT, ensuring both outbound and inbound connections are correctly routed between nodes

{% include details_close.html %}

{% include details_open.html title="Cloud Application Infrastructure" summary="Infrastructure provisioning and configuration for a cloud-native microservices app project. I owned the infrastructure design." %}

* **Context**: coursework project (pair programming), using Terraform
* **Verification**: local testing environment (kind, azurite), then deployed to Azure managed services, with infrastructure changes verified through integration tests
* **Availability**: private repository, code available on request

Key design decisions:

* **Compute provisioning**: allocation of application layers across cloud offerings, with stateful services on managed k8s and the stateless customer-facing endpoints on Azure App Service with autoscaling
* **Security**: moved application to isolated network connections using virtual network, to minimise exposure to public internet
* **Deployment**: moved from manual provisioning to full provisioning and teardown of infrastructure using Terraform, ensuring reproducible environments and configuration

{% include details_close.html %}

## Systems Programming

{% include details_open.html title="File Cache Server via IPC" summary="File cache service that provides a backing store for a proxy server, using shared memory IPC to provide file data to multiple concurrent processes." %}

* **Context**: coursework project, in C, using POSIX shared memory and message queue primitives, and cache invalidation out of scope
* **Verification**: integration test suite, checks with valgrind/helgrind
* **Availability**: private repository, code available on request

The file cache server provides an abstraction over the underlying file system, mitigating risk of file descriptor exhaustion, disk I/O management, and buffering content to lower latency for frequently-accessed files.

Key design decisions:

* **Inter-process coordination**: clear separation between command and data layers, with POSIX message queues used as a lightweight coordination primitive to coordinate the setup and teardown of shared memory segments
* **Safety**: direct communication of data bounds and use of coordination primitives to ensure safe reads/writes to shared memory.

{% include details_close.html %}

{% include details_open.html title="FunnelSort Implementation" summary="Implementation of cache-oblivious sorting algorithm, including a simplified memory layout for the recursive van Emde Boas tree structure. Includes public write-up of efficiency analysis and asymptotic bounds on efficiency loss at the link [here](/2026/10/05/funnelsort)." %}

* **Context**: coursework project, in C
* **Verification**: data reconciliation tests, checks with valgrind, cache-miss performance measured with cachegrind (66% cache miss reduction compared to naive mergesort)
* **Availability**: private repository, code available on request

{% include details_close.html %}

{% include details_open.html title="SampleSort Implementation" summary="Implementation of parallel sorting with regular sampling (PSRS) algorithm, for distributed sorting of large data sets." %}

* **Context**: coursework project, in C using MPI, with highly skewed keys de-scoped
* **Verification**: data reconciliation tests, checks with valgrind, sort performance measured by wall-clock on cluster (0.23s for 1.6GB data, distributed over 4 nodes and 64 processes)
* **Availability**: private repository, code available on request

{% include details_close.html %}

## Personal Projects

{% include details_open.html title="Website Testing Infrastructure" summary="Containerised test environment for this site, incorporating Playwright and other tests to support an AI-assisted site development workflow. Public write-up available [here](/2026/06/20/building)." %}


* **Context**: personal site and sandbox to develop skill in AI-augmented development
* **Verification**: automated regression suite, integrated with GitHub CI, with manual verification of major changes
* **Availability**: at [github](https://github.com/jrmylow/jrmylow.github.io)

Key design decisions:

* **Threat model**: data exfiltration is bounded through keeping secrets and sensitive information away from the test environment. The container serves to provide reasonable protection from agent-generated test code to the host and filesystem through rootless containers.
* **Reproducibility**: dependencies are pinned to match GitHub Pages workflow and ensure Playwright testing matches the end-user experience

{% include details_close.html %}
