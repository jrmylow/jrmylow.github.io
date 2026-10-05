---
layout: post
# Basic title information
title: A Simple Funnelsort Layout
summary:
 - p: How a small trick makes a complex algorithm easier to get right, with bounded performance penalties.

date: 5/10/2026
author: Jeremy Low
tags:
 - algorithm
 - HPC

toc: false
math: true

---

## Slow and Fast Things in Computers
Computer marketing tends to focus on clock speed and core count to convince you to pay for more performance. While it's not wrong per se, it leads people to underestimate how much of a difference other numbers like memory latency, bandwidth, and cache size make in real performance.

Why do I single out these operations? It's because the speed increases in CPUs have outstripped the speed increases in memory input/output (I/O) operations. Don't take my word for it - Brendan Gregg has an excellent writeup [here](https://www.brendangregg.com/blog/2017-05-09/cpu-utilization-is-wrong.html), showing how a real system is unable to fully utilise the CPU because it's being stalled on memory I/O:

> The key metric here is **instructions per cycle** (insns per cycle: IPC), which shows on average how many instructions \[...\] were completed for each CPU clock cycle. The higher, the better (a simplification). The above example of 0.78 sounds not bad (78% busy?) until you realize that this processor's top speed is an IPC of 4.0. This is also known as _4-wide_, referring to the instruction fetch/decode path. Which means, the CPU can retire (complete) four instructions with every clock cycle. So an IPC of 0.78 on a 4-wide system, means the CPUs are running at 19.5% their top speed.

These aren't small differences either, [Latency Numbers Every Programmer should Know](https://gist.github.com/jboner/2841832) has aged reasonably well. Relative to L1 cache (the fastest access):

* L2 cache is approximately 14x slower
* A main memory access is approximately 200x slower
* Fetching from an SSD is approximately 300,000x slower
* A network exchange over a fast datacenter network is approximately 1,000,000x slower
* Fetching from a hard drive is approximately 20,000,000x slower

Suffice to say, minimising the number of these "expensive" I/Os starts to matter for program performance, even today. GPU memory management and transfer scheduling is an active area of development with GPU bandwidth limitations, the need for a large KV cache, and variable input/output lengths spurring a revival of techniques from operating systems.

## Meeting in the Middle
Of course, most programmers don't have fine-grained control over their hardware, or even operating system. That said, it is still helpful to think about the real system when designing programs, and the amount of performance gains from raw algorithmic tuning can surprise people.

We are going to use a little math here, so let's get some definitions out of the way:

* We have some input data of size $$N$$ items that we want to operate on
* We have a cache of size $$M$$ items, and main memory of unlimited size, for our purposes
* When we carry out an I/O operation, we can bring $$B$$ items from memory to cache at once
* We can only compute things using items in our cache

By assumption, $$N$$ is much larger than $$M$$, therefore we will need to carry out many I/O operations for our full computation. Our goal, then, is to minimise the number of these operations while not compromising other aspects such as overall sorting time and memory usage.

For a comparison sorting algorithm, it turns out that a tuned multiway merge sort (an $$M/B$$-way merge to be precise) is able to achieve the information-theoretic optimal bound on memory transfers, with the following properties:

* **Memory transfers**: $$O((N/B) \log_{M/B} (N/B))$$ memory transfers[^1]
* **Comparisons**: $$O(N \log N)$$ comparisons
* **Memory footprint**: $$O(N)$$ additional memory

For comparison, a naive mergesort implementation has $$O((N/B) \log_2 (N/B))$$ memory transfers. The difference between the two (by the log change of base formula) is $$\log_2 (M/B)$$. This might not seem like much at first glance, but real numbers provide a better sense of scale. On modern architectures, cache line size is typically ~64 bytes. If an L2 cache is 1 MB, the naive algorithm is expected to use ~14x more memory transfers. It's even more drastic if we consider paged memory, using a typical page size of 4 kB and a system with 64GB of RAM as "cache", the naive algorithm can use ~24x more disk accesses by this estimate.

However, there is a tiny problem that snuck in, did you catch it?

If programmers don't have control over their hardware, or even know what hardware they are running on, how can they tune their algorithm? One option would be to try leaning on the operating system to give you those details. However, a family of algorithms called *cache-oblivious algorithms* is interesting because it promises to get comparable performance to algorithms that are tuned (*cache-aware algorithms*), without knowing anything about the underlying system.

*Funnelsort* is one such sorting algorithm, being comparable[^2] to the performance of tuned mergesort while being cache-oblivious. This doesn't come for free. The heart of funnelsort is a data structure called a *K-funnel*, storing data in a recursive layout called the van Emde Boas layout. Implementing the funnel is a source of [much pain](https://medium.com/@lemmon.warren/funnelsort-ef45c003b2d1) for implementers, as one account puts it:

> The main difficulty was an error-free van Emde Boas layout
> ...
> Whether you build the vEB-funnel top-down or bottom up, its a nightmare. If you build it topdown, you end up with nodes and buffers laid out in the wrong order. Then you have to traverse the tree and re-allocate the structure in the correct order. If you build it from bottom-up, you have to juggle pointers and predict buffer sizes ahead of time.

Let's unpack this layout to understand why it's tricky.
## Theoretical Funnels
To quote [Demaine's succinct description of a K-funnel](https://users-cs.au.dk/gerth/MassiveData02/notes/demaine.pdf):

> A $$K$$-funnel is a complete binary tree with $$K$$ leaves, stored according to the van Emde Boas layout. Thus, each of the recursive subtrees of a $$K$$-funnel is a $$\sqrt{K}$$-funnel. In addition to the nodes, edges in a $$K$$-funnel store *buffers* ... The edges at the middle level of a $$K$$-funnel, partitioning the funnel into two recursive $$\sqrt{K}$$-subfunnels, have size $$K^{3/2}$$ each, for a total buffer size of $$K^2$$ at that level. Buffers within the subfunnels are recursively smaller.

In short, you have a binary tree that you cut in half by *height* recursively, resulting in trees that are a square root of the original tree's size:

![A diagram demonstrating the recursive van Emde Boas layout]({{ '/public/img/2026-10-05/01-vEB-layout.png' | absolute_url }})

Demaine points out that while we could feed $$N = K$$ elements into a $$K$$-funnel, that doesn't make much sense because it allocates $$K^2$$ intermediate buffers. Therefore, we generally want to size a funnel so that $$N = K^3$$, both for speed and so that the total additional memory fits within our intended bound of $$O(N)$$.

Because we can, theoretically, know the footprint size from the number of input elements, this lends itself towards arena allocation in favour of repeated `malloc()` calls. In practice, the square roots tend to trip up implementers, which shouldn't be much of a surprise as even the comparatively simple binary search algorithm contains [edge cases](https://en.wikipedia.org/wiki/Binary_search#Implementation_issues) that get people in whiteboard interviews.

However, this approach assumes we construct $$K$$ from $$N$$ directly, which gives us ugly calculations. What if we didn't do that, and instead tried to construct "nice" $$K$$-funnels?
## An Idealised K-Funnel
It turns out that there are values of $$K$$ for which the funnel can be constructed beautifully. Consider a $$K$$ of the form $$K(i) = 2^{2^i}$$, where $$i$$ is the recursion level of the tree. We'll step through how this makes the problem easier to define in this section. For people who want to verify my calculations, I'll be providing python code and pseudocode for you to play with.

```python
def K(i):
    return 2**(2**i)
```

It turns out that computing $$\sqrt{K}$$ is easy for $$i >= 1$$, it's simply $$K(i-1)$$, see for yourself:

$$\sqrt{K(i)} = K(i)^{1/2} = \left(2^{2^i}\right)^{1/2} = 2^{2^i / 2} = 2^{2^{i-1}} = K(i-1)$$

It follows that $$K(i)^2$$ is simply $$K(i+1)$$ and $$K(i)^{3/2}$$ is simply $$K(i) \cdot K(i-1)$$.

This means that the memory layout for a $$K$$-funnel goes from something like this, allowing us to allocate memory across the funnel once:

```python
def Mem(K):
    if (K <= 2):
        return 0
    else:
        return K**2 + (sqrt(K) + 1) * Mem(sqrt(K))
```

To this:

```python
def Mem(i):
    if (i < 1):
        return 0
    else:
        return K(i+1) + (K(i-1) + 1) * Mem(i-1)
```

If $$i$$ is a natural number, so is $$2^i$$ and so is $$2^{2^i}$$. The exponentiation means that $$K(i)$$ results in a perfect binary tree[^3]. This allows someone to navigate the van Emde Boas tree through integer operations alone too.

The diagram below shows how this clean definition of $$K$$ earns its keep. Under the classic definition, one derives $$K$$ as a cube root of $$N$$, then applies square root operations as you recurse through the tree, a nightmare to track. On the other hand, this idealised $$K$$ has integer operations all the way through the tree by construction.

![A diagram demonstrating the equivalence of two formulations]({{ '/public/img/2026-10-05/02-k-equivalence.png' | absolute_url }})

Of course, this isn't the only way to navigate the tree. [Brodal et al. (2002)](https://www.cs.au.dk/~gerth/papers/soda02.pdf) use a precomputed table of size $$O(\log n)$$ to lay out a static tree to partition and navigate the data structure. One could even try variations of pointer-based approaches, as examined by [Vinther's 2003 Master's thesis](https://cs.au.dk/~gerth/advising/thesis/kristoffer-vinther.pdf), sidestepping index computation entirely. What this layout does provide is a structure that is relatively simple to reason about and to implement correctly, and this helped me immensely through my learning journey.

## The Ladder of Efficiency
It does help to understand what exactly this approach does cost in efficiency, though, to make tradeoffs with open eyes. To do this, let's use the diagram below, which shows the sweet spots and ranges of concern for various values of input size, $$N$$, relative to $$K(i)$$:

![A diagram demonstrating optimal funnel regions for various input sizes]({{ '/public/img/2026-10-05/03-sizing.png' | absolute_url }})

* **Undersized (red region)**: Under $$K(i)^2$$ we are undersized and occupying greater than $$O(N)$$ memory, so we should look for a smaller funnel.
* **Ideal sized (green region)**: From $$K(i)^2$$ to $$K(i)^3$$ we are in a sweet spot for a funnel of size $$K(i)$$, with memory in $$O(N)$$ and cache-optimal
* **Oversized (yellow region)**: From $$K(i)^3$$ to $$K(i)^4$$ we are in an awkward spot, for reasons outlined below
* **Ideal sized for next funnel**: From $$K(i)^4$$ to $$K(i)^6$$, we are in a sweet spot again, but for a funnel of size $$K(i+1) = K(i)^2$$, as per the first bullet

However, note that the oversized region for a $$K(i)$$ funnel runs up to the ideal sized region for the next funnel $$K(i+1)$$. By induction, we can infer that every $$N$$ either falls within the correctly sized or oversized regions for some $$K$$-funnel. We just need to understand what the performance characteristics of the algorithm are within this oversized region.

For argument's sake, let's use $$N = CK(i)^3$$ for some $$C$$ in the range $$(1, K(i))$$ that clearly lands in the oversized region for $$K(i)$$. For a $$K(i)$$-funnel that wants an input of $$N = K(i)^3$$, the funnel might not be optimal if overfed. On the other hand, allocating up to $$K(i+1)^2 = K(i)^4$$ memory in the case of the $$K(i+1)$$ funnel is wasteful because each leaf wants $$K(i+1)^2 = K(i)^4$$ input elements, but is only getting $$CK(i)$$, which is less than even $$K(i)^2$$. It's not obvious at first glance which is the better approach.

## Fundamental Transfer Costs
Fortunately, we don't have to guess. The theoretical work from [Brodal and Fagerberg](https://link.springer.com/chapter/10.1007/3-540-45465-9_37) comes to our rescue here, and we'll take a deep dive to understand what makes funnelsort cache-optimal to begin with. One nuance from this paper, though, is that they introduce a parameter $$d$$ where $$N = K^d$$, which carries through this derivation (in our case, $$d=3$$).

To understand the algorithm costs, we need to understand how many transfers it takes to merge a single $$K$$-funnel.

One concept I'll borrow from the paper is $$\bar{k}$$ (small k, for ease of reading), which is the largest $$k$$ such that the $$k$$-funnel and cache lines from each leaf fit in cache (following the paper's limit of $$M/2c$$). Since, by construction, such a $$\bar{k}$$-funnel is fed by buffers larger than $$\bar{k}$$, it follows that these *large buffers* do not completely fit into cache. Therefore, a funnel is a series of $$\bar{k}$$-trees (each of which fits in cache) fed by large buffers (that do themselves not fit in cache).

**Result 1: the cost to merge elements depends on the funnel size, not the input size**. The proof of Lemma 1 in the paper is direct. A single call outputs at least $$\bar{k}^d$$ elements to the output buffer, with a per-element cost of $$O(\log_M (\bar{k}^d))$$ insertions into large buffers, a cost of $$1/B$$ I/O operations per large buffer insertion, and $$\log_M(K^d)$$ large buffer crossings as it moves through the funnel. Note that this is only dependent on the *size of the funnel* $$K$$, and not a property of the input data. Therefore, we can scale this to consider the total cost for the whole funnel as the product of:

* $$N$$, the number of elements driven through the $$K$$-funnel - we separate this out because our funnels are not exactly sized to N
* $$1/B$$, the I/O per element per buffer movement
* $$\log_M (K^d)$$ which is the number of buffer movements per element

From this, we can derive three results for a funnel of size $$K(i)$$, with $$K(i)$$ input buffers as leaves, and $$1 < C < K$$:

* **Base Case**: a correctly sized $$K$$-funnel with $$N=K(i)^3$$ input data ($$K^2$$ per leaf) requires $$O((K(i)^3/B) \cdot \log_{M} (K(i)^3))$$ memory transfers
* **Under-driven**: a $$K$$-funnel with $$N=CK(i)^2$$ input data ($$CK$$ per leaf) requires $$O((CK(i)^2/B) \cdot \log_{M} (K(i)^3))$$ memory transfers
* **Over-driven**: a $$K$$-funnel with $$N=CK(i)^3$$ input data ($$CK^2$$ per leaf) requires $$O((CK(i)^3/B) \cdot \log_{M} (K(i)^3))$$ memory transfers

When we consider the merge through a *single funnel only* (instead of the full sort), we can see where the inefficiency in under-driven funnels comes from. In all cases for a fixed-size $$K(i)$$-funnel, the cost to move an element through the funnel is $$\log_M(K(i)^3)$$, where we would expect $$\log_M(CK(i)^2)$$ for when $$K$$ is matched to the input size $$N$$. The ratio is $$3 \log_M(K) / (\log_M{C} + 2\log_M{K})$$, which collapses to $$3/2$$ as $$C \rightarrow 1$$.

Of course, we aren't just interested in one funnel's worth of transfers, because the merge depends on sorted input buffers. Fortunately, the algorithm is recursive, which lets us reason about the full cost.

## Full Algorithm Costs
Part of the beauty in funnelsort, which I won't go into here, is how the algorithm to fill buffers works together with the data structure to minimise memory transfers. What I will go into, though, is the fact that we have a spectrum of choices in how we carve up the dataset for the full sorting algorithm. For an input size of $$N = CK(i)^3$$ there are two extreme points:

* One $$K$$-funnel at the top, fed by $$K$$ buffers of size $$CK^2$$ (underfed buffers for $$K$$-funnels); or
* One $$C$$-funnel at the top (or as close as we can get), fed by $$C$$ buffers of size $$K^3$$ (fully fed buffers for $$K$$-funnels)

The recurrence relationship for the total cost is simply the cost to merge sorted buffers (which we've calculated), plus the cost to sort the input buffers. In Theorem 2 of Brodal and Fagerberg's paper, they show that the number of I/Os per element is given by the formula below:

$$
O(\frac{1}{B}(1 + \sum_{i=0}^{\infty} \log_M N^{(1-1/d)^i})) = O(d \log_M(N)/B)
$$

At first glance, this looks like it depends on the input size $$N$$. However, we can follow the proof and build up from Lemma 1 of the paper to convert the expressions to be based on $$k$$, with $$N^{1/d}=K$$ and $$N^{1-1/d} = K^{d-1}$$. As such, we expose the fact that again, the per-element sorting cost is *dependent on the funnel structure only*.

This makes our life significantly easier, because we can rely on this to reason about our per-element sorting cost, and hence our total sorting cost, as follows. The memory transfers per element is simply the sum of:

* A term for the mandatory movement (all elements must be loaded into cache at some point)
* A term for the top funnel (for our purposes, a $$K$$-funnel or a $$C$$-funnel)
* A term for the recursive sort through the $$K$$-funnels that feed the top funnel, which are identical to Theorem 2's result and are *already cache-optimal sorts*.

We convert Theorem 2's formula into $$K$$ for the purposes of our analysis, use $$d=3$$, and pull the exponent out of the log term:
$$
O(\frac{1}{B}(1 + \sum_{i=0}^{\infty} (\frac{2}{3})^i \log_M K^3))
$$
The sum of the infinite geometric series is simply 3, which is nice for our purposes. We can now add the term for the top funnel from here. In the case of a $$K$$-funnel at the top:
$$
O(\frac{1}{B}(1 + \log_M K^3 + \sum_{i=0}^{\infty} (\frac{2}{3})^i \log_M K^3))
$$
This simplifies to the following, dropping the constant term:
$$
O(\frac{1}{B}(4\log_M K^3))
$$
On the other hand, if we have a $$C$$-funnel at the top:
$$
O(\frac{1}{B}(1 + \log_M C^3 + \sum_{i=0}^{\infty} (\frac{2}{3})^i \log_M K^3))
$$
This simplifies to the following result by dropping the constant term:
$$
O(\frac{1}{B}(1 + \log_M C^3 + 3\log_M K^3)) = O(\frac{1}{B}(3 \log_M (CK^3)))
$$
This leads to the finding that using a $$K$$-funnel at the top incurs slightly more transfers, by a factor of:
$$
\frac{4\log_M K^3}{3\log_M CK^3} = \frac{4 \log_M(K)}{\log_M(C) + 3 \log_M(K)}
$$
**Result 2: it is always more efficient to use a $$C$$-funnel than a $$K$$-funnel**. Because $$1 < C < K$$, we can see that the first approach, using $$K$$ as the initial funnel size is at best as good as using $$C$$ (in the case when $$C = K$$) and at worst $$4/3$$ times the total memory transfers, a sizeable 33% difference.

Incidentally, this analysis also demonstrates that the use of a $$C$$-funnel at the top achieves the intended sorting lower bound for memory transfers, since converting it to N satisfies the per-merge lower bound from Brodal and Fagerberg exactly:
$$
O(\frac{1}{B}(3 \log_M (CK^3))) = O(d \log_M(N)/B)
$$
Of course, we cannot always achieve a result where $$C$$ forms an idealised funnel, but by minimising the value of $$C$$, this minimises the unit cost of a merge through the funnel. We can minimise the inefficiency by choosing the smallest $$C' > C$$ such that $$C'= K(j)$$ for some $$j$$, in the spirit of wanting exact funnels throughout. Because $$C'$$ is at most $$K(i)$$, the asymptotic performance of this approach is at most 33% worse off compared to using exact roots.

## Conclusions
Funnelsort is an intimidating algorithm to implement straight from the paper. I certainly struggled with the idea of using square roots and handling the memory management calculations, and using perfect funnels made memory management significantly easier, at a price of less memory transfer efficiency.

That price, a potential 33% increase over the optimal result, is small relative to the potential for 14-24x increases over the cache-optimal result that naive merge sort pays, but it isn't nothing. If you are implementing your own funnelsort (for whatever reason), I hope that this analysis helps save you some pain and gives a clearer cost of the tradeoffs of computing time vs programmer time.


[^1]: Based on the "tall cache" assumption, that $$M > B^2$$.
[^2]: Specifically on the number of memory transfers, asymptotically, within a constant factor
[^3]: The number of buffers ($$k - 2$$) and binary mergers ($$k - 1$$) is also fully known to begin with and trivial to calculate, another nice result of the perfect binary tree
