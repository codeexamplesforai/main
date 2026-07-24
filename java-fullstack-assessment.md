# Java Full Stack (Backend-Heavy) — Interview Assessment Bank
### Levels: AVP and Assistant Manager · Duration: ~60 minutes

---

## How to use this pack

Eight sections. **Pick exactly one question from each section.** Time budgets add to 60 minutes.

| # | Section | Time | Focus |
|---|---------|------|-------|
| A | Core Java & JDK 21+ | 8 min | Concurrency, memory model, virtual threads |
| B | Collections & Data Structures | 6 min | Internals, correct structure choice |
| C | Spring Ecosystem | 8 min | Boot, Security, Data JPA, Batch/MVC/Integration |
| D | Database & Persistence | 8 min | SQL, indexing, transactions, JPA tuning |
| E | Frontend | 8 min | React/Angular, TS, performance, browser security |
| F | Threading — Logic & Math | 7 min | Pool sizing, Amdahl, Little's Law |
| G | Collections — Logic & Math | 7 min | Complexity, resize cost, sizing |
| H | Memory Burn & CPU Cycles | 8 min | Allocation rate, GC cadence, cycle budgets |

**Level markers:** `[AVP]` = deeper/architectural · `[AM]` = solid working depth · `[BOTH]` = scales with the answer.

**Scoring (per section, 0–4):** 0 no answer · 1 memorised definition · 2 correct but shallow · 3 correct with trade-offs · 4 correct, quantified, and connected to production experience.
Suggested bar: **AVP ≥ 24/32**, **Assistant Manager ≥ 18/32**.

---

## Section A — Core Java & JDK 21+ *(8 min, pick 1)*

### A1. `[BOTH]` Virtual threads vs. platform threads — when do they *not* help?

**Answer.** A virtual thread is a lightweight thread scheduled by the JVM onto a small pool of carrier (platform) threads. When it blocks on most JDK I/O, the JVM *unmounts* the continuation from the carrier and parks it on the heap, so the OS thread is free. Cost is roughly a few hundred bytes to a few KB versus ~1 MB of reserved stack per platform thread.

They help when the workload is **I/O-bound with high concurrency** — thousands of blocking HTTP/JDBC calls. They do **not** help when:
- The work is **CPU-bound**. You still only have N cores; you cannot exceed them by making more threads.
- The thread **pins** the carrier — inside a `synchronized` block that blocks, or in a native/JNI call. Fix: replace `synchronized` with `ReentrantLock`.
- The real bottleneck is a downstream limit (a 20-connection DB pool doesn't get faster because 10,000 virtual threads are queueing on it — you just move the queue).

Also: don't pool virtual threads. Use `Executors.newVirtualThreadPerTaskExecutor()`; they're meant to be disposable.

**Follow-up:** How would you detect pinning? *(JFR event `jdk.VirtualThreadPinned`, or `-Djdk.tracePinnedThreads=full`.)*

---

### A2. `[AVP]` Explain the Java Memory Model guarantees behind `volatile` and why `synchronized` gives you more.

**Answer.** The JMM defines a *happens-before* partial order. Without it, the compiler, CPU, and caches may reorder or hide writes.

`volatile` gives:
- **Visibility** — a write is flushed and any subsequent read sees it, no caching in registers.
- **Ordering** — a volatile write acts as a release barrier, a volatile read as an acquire barrier. Everything written *before* the volatile write is visible to a thread that reads that volatile.
- **Atomicity only for single reads/writes**, including `long`/`double`. It does **not** make `count++` atomic — that's read-modify-write, three operations.

`synchronized` adds **mutual exclusion** on top of the same visibility/ordering guarantees, so compound actions become atomic. `AtomicInteger` sits in between: lock-free CAS gives atomic read-modify-write without blocking, better under moderate contention; under very high contention `LongAdder` wins by striping across cells.

**Follow-up:** Double-checked locking without `volatile` on the field — what breaks? *(Another thread can see a non-null but partially constructed object due to reordering of allocation and field initialisation.)*

---

### A3. `[AM]` Given a `CompletableFuture` chain that calls three services, how do you handle timeouts, fallbacks, and thread pools correctly?

**Answer.** Key points to hear:
- Use `supplyAsync(task, customExecutor)` — never let it default to the common ForkJoinPool for blocking I/O, because you'll starve every other parallel stream in the JVM.
- Parallel fan-out: `CompletableFuture.allOf(a, b, c).thenApply(...)` — total latency is the *max*, not the sum.
- Per-call timeout: `orTimeout(2, SECONDS)` (fails) or `completeOnTimeout(default, ...)` (degrades).
- Fallback: `exceptionally(ex -> default)` or `handle((v, ex) -> ...)`. Note `exceptionally` receives a `CompletionException` wrapper — unwrap `getCause()`.
- Bulkhead: separate executor per downstream so one slow dependency can't consume all threads.
- Don't call `.join()` inside a stage running on the same pool — self-deadlock risk on bounded pools.

**Follow-up:** How does this change with virtual threads? *(Often simpler: structured concurrency with `StructuredTaskScope.ShutdownOnFailure` gives you scoped cancellation and error propagation without the callback chain.)*

---

### A4. `[AVP]` G1 vs. ZGC — how do you choose, and what do you tune?

**Answer.**

| | G1 | ZGC |
|---|---|---|
| Pause target | ~50–200 ms, scales with live set | Sub-millisecond, independent of heap size |
| Best heap | Up to ~32 GB | Large heaps, 10 GB–TB |
| Throughput | Higher | ~5–15% throughput cost |
| Mechanism | Regionised, concurrent mark + evacuation pauses | Fully concurrent, coloured pointers + load barriers |

Choose **G1** for typical microservices where 100 ms p99 GC pauses are acceptable and throughput matters. Choose **ZGC** (generational, JDK 21+) when tail latency is the SLA — trading, real-time bidding, or heaps too big for G1 to evacuate cheaply.

G1 tuning knobs that actually matter: `-XX:MaxGCPauseMillis`, `-XX:G1HeapRegionSize`, `-XX:InitiatingHeapOccupancyPercent`, and above all **fixing allocation rate in the code**. Reflexively setting `-Xmn` on G1 is usually a mistake — it disables adaptive young sizing.

**Red flag answer:** "We increased the heap." Ask what the *allocation rate* and *promotion rate* were.

---

## Section B — Collections & Data Structures *(6 min, pick 1)*

### B1. `[BOTH]` Walk through what happens inside `HashMap` on `put()` — including collisions and resize.

**Answer.**
1. `hash(key)` = `h ^ (h >>> 16)` — spreads high bits down, because the index is `hash & (n-1)` and only low bits would otherwise be used.
2. Index into `table[i]`. If empty, create a `Node`.
3. If occupied: compare `hash` first (cheap int compare), then `==`, then `equals()`. Match → replace value. No match → append to the bin.
4. **Treeification:** when a bin reaches 8 entries *and* table capacity ≥ 64, the bin converts to a red-black tree — worst case goes from O(n) to O(log n). Below capacity 64 it resizes instead. Untreeifies at 6 (hysteresis).
5. **Resize:** when `size > capacity × 0.75`, capacity doubles and entries are rehashed. Because capacity is a power of two, an entry either stays at index `i` or moves to `i + oldCap` — Java 8+ splits each bin into a "lo" and "hi" list without recomputing hashes.

**Follow-up:** Why must a key be immutable? *(If a field used by `hashCode()` changes after insertion, the entry sits in the wrong bin and becomes unreachable — a silent leak.)*

---

### B2. `[AVP]` `ConcurrentHashMap` vs. `Collections.synchronizedMap` — mechanism and failure modes.

**Answer.** `synchronizedMap` wraps every method in one monitor on a single object: all readers and writers serialise. Throughput is flat regardless of core count, and iteration requires the caller to hold the lock manually.

`ConcurrentHashMap` (Java 8+) has **no segments** any more. It uses:
- CAS to install the first node in an empty bin (lock-free fast path),
- `synchronized` on the *bin head* for contended writes — lock granularity is one bucket,
- fully **lock-free reads** via `volatile` node fields,
- **cooperative resizing** — multiple writer threads help transfer bins,
- `LongAdder`-style striped counters for `size()`, so `size()` is an estimate.

Failure modes candidates should name:
- **Not atomic across operations.** `if (!map.containsKey(k)) map.put(k, v)` is a race. Use `putIfAbsent`, `computeIfAbsent`, or `merge`.
- **Don't do blocking I/O or acquire other locks inside `computeIfAbsent`** — you hold the bin lock; recursive updates on the same map throw or deadlock.
- Iterators are **weakly consistent**, not snapshot and not fail-fast.
- No `null` keys or values (ambiguity between "absent" and "mapped to null" in a concurrent context).

---

### B3. `[AM]` You need a lookup of 5 million records by ID, read-heavy, occasional updates. Compare your options.

**Answer.** Expect the candidate to reason about layout, not just names:
- `HashMap` — O(1) average, but 5M boxed entries is a large object graph and a GC scanning cost. Pre-size it: `new HashMap<>(8_000_000)` to avoid ~19 resizes.
- `ConcurrentHashMap` — same, plus safe concurrent access. Default choice for read-heavy with writes.
- `TreeMap` — only if you need range queries or ordering; O(log n) with poor cache locality (pointer chasing).
- **Primitive/open-addressing map** (Eclipse Collections, fastutil, Agrona) — if keys are `long`/`int`, this removes boxing entirely and can cut footprint by 5–10× (see Section H).
- **Off-heap / Chronicle Map or a cache like Caffeine** — if the working set won't fit or must survive restarts.
- `CopyOnWriteArrayList` / `COWMap` patterns — only for near-zero write rates; every write copies the backing array.

Strong answer names the actual constraint: is this bounded by memory, by lookup latency, or by GC pressure from the object graph?

---

### B4. `[AVP]` What's wrong with this code, and how many ways can it fail?

```java
List<Order> orders = new ArrayList<>(shared);
for (Order o : orders) {
    if (o.isCancelled()) orders.remove(o);
}
```

**Answer.** At least four distinct problems:
1. **`ConcurrentModificationException`** — structural modification during iteration invalidates `modCount`. Correct: `orders.removeIf(Order::isCancelled)`, or an explicit `Iterator.remove()`.
2. **The one case where it *doesn't* throw is worse** — removing the second-to-last element makes `hasNext()` return false early, so the loop exits silently having skipped an element. A quiet correctness bug.
3. **O(n²)** — each `ArrayList.remove(Object)` is a linear scan plus an `System.arraycopy` shift.
4. `remove(Object)` uses `equals()`; if `Order` doesn't override `equals`/`hashCode`, it removes by identity, which may not be what was intended.

If `shared` is concurrently mutated, the copy constructor itself can also see a torn state.

---

## Section C — Spring Ecosystem *(8 min, pick 1)*

### C1. `[AVP]` Design the security model for a service exposed to a mobile app, an internal service, and a partner. OAuth2, JWT, mTLS, zero-trust.

**Answer.** Expect a layered answer:
- **Mobile app → Authorization Code + PKCE.** Never the implicit or password grant. Short-lived access token (5–15 min), rotating refresh token. Token in memory, refresh token in secure device storage.
- **Service → service (internal): mTLS**, ideally with certs issued and rotated by a mesh/SPIFFE identity. Identity comes from the certificate, not a shared secret.
- **Partner → Client Credentials grant**, scoped tokens, per-partner rate limits and audience claims.
- **Resource server config:** `oauth2ResourceServer().jwt()` with a JWKS URI, validate `iss`, `aud`, `exp`, and signature. Cache JWKS with a refresh on unknown `kid`.
- **Zero-trust means:** authenticate and authorise at *every* hop, no implicit trust from being inside the network, least privilege on scopes, and short token lifetimes so revocation windows are small.
- **JWT trade-off to name:** stateless validation means you can't revoke instantly. Mitigations: short TTL, a denylist for the TTL window, or opaque tokens with introspection where revocation matters more than latency.
- **Method-level:** `@PreAuthorize("hasAuthority('SCOPE_orders.write')")` for coarse checks plus domain-level ownership checks — scope alone doesn't prove *this* user owns *this* order.

**Follow-up:** When is CSRF protection needed and when is it noise? *(Needed for cookie-based sessions; largely irrelevant for a stateless API using an `Authorization` header, which is why it's commonly disabled there.)*

---

### C2. `[AM]` Explain Spring Boot auto-configuration. How do you debug a bean that isn't being created?

**Answer.** `@SpringBootApplication` includes `@EnableAutoConfiguration`, which loads candidate configuration classes listed in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (formerly `spring.factories`). Each is gated by `@Conditional` annotations: `@ConditionalOnClass`, `@ConditionalOnMissingBean`, `@ConditionalOnProperty`, `@ConditionalOnBean`. `@ConditionalOnMissingBean` is the reason your own `@Bean` silently wins over the default — auto-config is *backing off*, and it runs after user config.

Debugging tools:
- `--debug` or `debug=true` prints the **condition evaluation report**: positive matches, negative matches, exclusions. This is the answer to "why is my bean missing".
- `/actuator/beans` and `/actuator/conditions`.
- `@ConditionalOnMissingBean` ordering issues → check `@AutoConfiguration(after = ...)`.
- Common real causes: the class isn't in a scanned package, a missing starter on the classpath, a profile not active, or two beans of the same type without `@Primary`/`@Qualifier`.

---

### C3. `[AM]` Spring Batch, Spring MVC, or Spring Integration — pick one and explain its core model plus one production pitfall.

**Answer (any one, judged on depth):**

**Spring Batch** — Job → Step → (ItemReader, ItemProcessor, ItemWriter), chunk-oriented with commit interval N. `JobRepository` persists execution metadata, enabling restart from the last committed chunk. Pitfalls: choosing chunk size blindly (too small = transaction overhead per chunk, too large = long-held locks and a big rollback), non-restartable readers, and running the same `JobParameters` twice (Batch treats it as the same instance and refuses). Scaling: partitioning or remote chunking, not just bigger heap.

**Spring MVC** — `DispatcherServlet` → `HandlerMapping` → `HandlerAdapter` → controller → `ViewResolver`/`HttpMessageConverter`. Thread-per-request on a servlet container. Pitfalls: blocking calls exhausting the Tomcat pool (default 200 threads), and `@Transactional` on a self-invoked private method silently doing nothing because the proxy is bypassed.

**Spring Integration** — Message (payload + headers) flowing across Channels through Endpoints (transformer, filter, router, service activator). Pitfalls: unbounded `QueueChannel` growth, and losing messages on a non-persistent channel during restart — needs a durable broker if delivery matters.

---

### C4. `[AVP]` A JPA repository method is issuing 4,000 queries per request. Diagnose and fix.

**Answer.** Classic **N+1**: one query for the parent collection, one per lazy association touched.

Diagnosis: enable `spring.jpa.show-sql` plus `hibernate.generate_statistics`, or better, use a datasource proxy (p6spy/datasource-proxy) to count queries per request. Assert the count in an integration test so it can't regress.

Fixes, in order of preference:
1. **`JOIN FETCH`** in a JPQL query, or an **`@EntityGraph`** on the repository method — declarative, doesn't pollute the mapping.
2. **`@BatchSize(size = 50)`** — turns N queries into N/50 `IN (...)` queries. Good when you can't restructure.
3. **DTO projection** — `select new com.x.OrderView(o.id, c.name) from Order o join o.customer c`. Best when you only need a few columns; avoids hydrating entities into the persistence context at all.
4. Never `FetchType.EAGER` on collections as a global fix — it just moves the problem and breaks unrelated queries.

**Trap to probe:** `JOIN FETCH` on **two** collections at once produces a Cartesian product. Fetch one collection plus scalars, then a second query, or use `@BatchSize`. Also: `JOIN FETCH` + pagination makes Hibernate paginate **in memory** (`HHH000104` warning) — a silent OOM on large tables.

**Follow-up:** What are `@QueryHints` good for? *(`org.hibernate.readOnly` skips dirty-checking snapshots on read-only queries — real memory and CPU savings on large result sets; `jakarta.persistence.query.timeout` bounds runaway queries; `hibernate.fetchSize` controls JDBC cursor batching.)*

---

## Section D — Database & Persistence *(8 min, pick 1)*

### D1. `[AM]` Write a query for: per customer, their top 3 orders by value, plus a running total of their spend. Then explain the plan.

**Answer.**
```sql
WITH ranked AS (
  SELECT o.customer_id,
         o.order_id,
         o.amount,
         ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.amount DESC) AS rn,
         SUM(o.amount) OVER (PARTITION BY o.customer_id
                             ORDER BY o.created_at
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
  FROM orders o
  WHERE o.created_at >= DATE '2026-01-01'
)
SELECT * FROM ranked WHERE rn <= 3 ORDER BY customer_id, rn;
```
Points to probe: why `ROW_NUMBER` and not `RANK` (ties), why the filter is outside the CTE (window functions are evaluated after `WHERE` in the same query block), and the default window frame (`RANGE UNBOUNDED PRECEDING`) behaving differently from `ROWS` when there are duplicate `ORDER BY` values.

**Plan:** ideally an index on `(customer_id, amount DESC)` or `(customer_id, created_at)` lets the sort be satisfied by the index, turning a Sort node into an Index Scan. Otherwise it's a full scan plus a sort per partition, which spills to disk once it exceeds `work_mem`.

---

### D2. `[AVP]` Clustered index vs. secondary index vs. inverted index vs. columnar storage — when does each win?

**Answer.**
- **Clustered index** — the table *is* the B-tree, ordered by the key (InnoDB PK, SQL Server clustered index). Range scans on the key are sequential I/O. Cost: a random-ish PK (UUIDv4) causes page splits and fragmentation; use auto-increment, UUIDv7, or ULID.
- **Secondary index** — separate B-tree holding the key + a pointer to the row (in InnoDB, the PK value). A lookup is index seek → PK seek, hence the value of **covering indexes** (`INCLUDE`) that avoid the second hop.
- **Inverted index** — term → posting list of doc IDs. Wins for full-text and multi-valued attributes (`GIN` in Postgres, Lucene/Elasticsearch). A B-tree can't answer "documents containing 'refund'" efficiently.
- **Columnar** (Parquet, ClickHouse, Redshift) — stores each column contiguously. Wins for analytics: you read only the columns you touch, compression is 5–20× better because values are homogeneous, and vectorised execution is cache-friendly. Loses badly for single-row OLTP writes and point updates.

Rule of thumb: **row store for many columns of few rows (OLTP), column store for few columns of many rows (OLAP).**

**Follow-up:** Selectivity. An index on a boolean `is_active` column where 95% are true is usually ignored by the planner — a full scan is cheaper than 95% random I/O.

---

### D3. `[AM]` Explain isolation levels and which anomaly each prevents. Then: what does `@Transactional` actually do?

**Answer.**

| Level | Dirty read | Non-repeatable read | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | possible | possible | possible |
| READ COMMITTED | prevented | possible | possible |
| REPEATABLE READ | prevented | prevented | possible* |
| SERIALIZABLE | prevented | prevented | prevented |

*InnoDB's REPEATABLE READ prevents phantoms in practice via gap locks; Postgres's REPEATABLE READ is snapshot isolation and prevents them for reads but allows write skew, which only SERIALIZABLE catches.

`@Transactional` creates a **proxy** that opens a transaction before the method and commits/rolls back after. Things candidates must know:
- **Self-invocation doesn't work** — an internal `this.method()` call bypasses the proxy entirely.
- **Default rollback is on unchecked exceptions only.** A checked exception commits unless you set `rollbackFor`.
- `REQUIRES_NEW` uses a *second* connection — two connections held simultaneously, which can deadlock a small pool.
- Transaction scope should not span external HTTP calls; you're holding a DB connection and locks for the duration of someone else's latency.

**Follow-up:** Optimistic (`@Version`) vs. pessimistic (`SELECT ... FOR UPDATE`) locking — optimistic for low contention and long think-time; pessimistic for short, hot, high-contention updates like inventory decrements.

---

### D4. `[AVP]` CAP and PACELC applied to a real decision: your order service writes to a primary with two async replicas. What are you actually choosing?

**Answer.** Under a network partition you choose availability or consistency; with async replication you have already chosen **AP** — a replica may serve stale data, and a failover can lose the un-replicated tail (a real data-loss window equal to replication lag).

PACELC is the more useful framing: *even when there is no partition (Else), you trade Latency vs. Consistency.* Async replication = low latency, eventual consistency. Sync replication = higher write latency, stronger consistency.

Practical mitigations to look for:
- **Read-your-writes**: route a user's reads to the primary for N seconds after their write, or pass an LSN/sequence token the replica must have caught up to.
- Bound acceptable staleness explicitly and monitor replication lag as an SLO, alerting before it exceeds the bound.
- Use **semi-synchronous** replication (ack from at least one replica) to shrink the loss window at modest latency cost.
- Idempotency keys so retries after a failover don't double-charge.

**Weak answer:** reciting "consistency, availability, partition tolerance — pick two" with no application.

---

## Section E — Frontend *(8 min, pick 1)*

### E1. `[BOTH]` Explain React's rendering model, and when `useMemo` / `useCallback` / `React.memo` genuinely help.

**Answer.** A state update marks a component dirty; React re-renders it and its subtree, produces a new element tree, diffs it against the previous one, and applies the minimum set of DOM mutations. **Re-render ≠ DOM update** — the diff usually results in very few real mutations, which is why most memoisation is premature.

Memoisation helps when:
- `React.memo` on a child that receives **stable** props and has an expensive subtree. Useless if you pass a fresh object/array/arrow literal each render — hence `useCallback`/`useMemo` on those props.
- `useMemo` around a genuinely expensive computation (sorting 10k rows, parsing), not around `a + b`.
- Referential stability for a value used in another hook's dependency array — otherwise the effect fires every render.

It hurts when: the comparison and cache cost exceeds the render cost, and when dependency arrays are wrong, producing stale closures. Better first moves are usually **lifting state down**, splitting components so updates have a smaller blast radius, `key`-based reconciliation fixes, and virtualisation for long lists.

**Follow-up:** Why is `key={index}` a bug in a reorderable list? *(React matches by key; index keys make it think item 3 changed content rather than moved, so component state and DOM focus attach to the wrong row.)*

---

### E2. `[AVP]` Where do you store an access token in a browser, and why?

**Answer.** There is no perfect option — expect the trade-off, not a slogan.

- **`localStorage`** — readable by any JS on the page. One XSS and every token leaks. Persists across tabs and restarts. Commonly used, commonly criticised.
- **`sessionStorage`** — same XSS exposure, smaller blast radius in time and scope.
- **JS memory only** — not readable by a separate XSS payload after page reload, lost on refresh, so needs a silent refresh flow. Better than either storage API.
- **`HttpOnly; Secure; SameSite=Strict/Lax` cookie** — invisible to JS, so XSS can't exfiltrate it. But it's sent automatically, so you now need CSRF protection (double-submit token or `SameSite`). Generally the **strongest default**, and the pattern behind BFF/token-handler architectures.

The honest framing: **if you have XSS, you have lost.** Cookies stop *exfiltration*, not *use* — an attacker can still make requests from the victim's browser. So the real controls are a strict **CSP**, output escaping, avoiding `dangerouslySetInnerHTML`, dependency scanning, and short token lifetimes.

**Follow-up:** What does CORS actually protect? *(Not the server. It relaxes the browser's same-origin policy for JS reading cross-origin responses. It is not authorisation, and `Access-Control-Allow-Origin: *` with credentials is rejected by browsers for good reason.)*

---

### E3. `[AM]` A dashboard takes 6 seconds to become interactive. How do you diagnose and fix it?

**Answer.** Measure before changing anything: Lighthouse / WebPageTest, Chrome Performance panel, and field data (RUM) for LCP, INP, CLS.

Diagnose along the waterfall:
- **Network** — bundle size, uncompressed assets (no Brotli), too many round trips, no HTTP/2, render-blocking CSS/JS in `<head>`.
- **Render** — a single 2 MB JS bundle parsed on the main thread; long tasks over 50 ms blocking input.
- **Data** — waterfalled API calls (fetch A, then B, then C) instead of parallel; no caching.

Fixes, roughly by impact:
1. **Code splitting** — route-level `React.lazy` / dynamic `import()`. Analyse with `source-map-explorer`; look for moment.js, lodash imported wholesale, duplicate React copies.
2. **Server-side render or stream the shell** so first paint isn't gated on JS.
3. **Parallelise or batch API calls**; move aggregation to a BFF so the browser makes one request instead of nine.
4. **Virtualise** long tables/lists — render 30 rows, not 5,000.
5. **Preload** critical fonts/assets; `font-display: swap` to avoid invisible text.
6. Cache: HTTP caching, ETags, SWR/React Query with stale-while-revalidate.
7. Reserve space for images/ads to fix CLS.

Strong candidates name a *target* (e.g. LCP < 2.5 s, INP < 200 ms) and say how they'd stop the regression returning (bundle-size budget in CI).

---

### E4. `[AM]` Angular: explain change detection and how `OnPush` plus RxJS changes the picture.

**Answer.** Zone.js monkey-patches async APIs (events, timers, XHR). When one fires, Angular runs change detection over the **whole component tree**, comparing template bindings, top-down. Default strategy checks every component every cycle.

`ChangeDetectionStrategy.OnPush` tells Angular to skip a component unless:
- an `@Input` reference changes (reference, not deep equality — mutating an array in place won't trigger it),
- an event originates from the component or its children,
- an `async` pipe in its template emits,
- `markForCheck()` is called explicitly.

With OnPush, the idiomatic pattern is immutable inputs plus observables rendered via `| async`, which also auto-unsubscribes and prevents the classic memory leak from manual `.subscribe()` in `ngOnInit` without `takeUntilDestroyed()`.

RxJS points worth probing: `switchMap` for typeahead (cancels the in-flight request — prevents out-of-order results), `mergeMap` when all results matter, `concatMap` when order matters, `exhaustMap` for submit buttons (ignores clicks while in flight). And `debounceTime` + `distinctUntilChanged` before the switchMap.

**Follow-up:** Signals in modern Angular remove the Zone.js dependency and make reactivity fine-grained — updates target the exact bindings that depend on the signal rather than walking the tree.

---

## Section F — Threading: Logic & Math *(7 min, pick 1)*

> Candidates may use a whiteboard. Marks are for the **method and the assumptions**, not arithmetic precision.

### F1. `[BOTH]` Thread pool sizing

*Your service runs on a pod with **8 vCPUs**. Each request spends **5 ms** on CPU (JSON, mapping, business logic) and **45 ms** waiting on a database and a downstream API. You want ~80% CPU utilisation. How many threads in the pool? What throughput does that give? What if you move to virtual threads?*

**Answer.** Use Brian Goetz's formula:

```
N_threads = N_cpu × U_target × (1 + W/C)
```
- `N_cpu = 8`, `U_target = 0.8`, `W/C = 45/5 = 9`

```
N_threads = 8 × 0.8 × (1 + 9) = 64 threads
```

**Throughput check (Little's Law, L = λ × W):**
Each request occupies a thread for 50 ms, so one thread serves 20 req/s.
```
λ = 64 threads / 0.050 s = 1,280 req/s
```
Sanity-check against the CPU ceiling: 8 cores ÷ 5 ms CPU per request = 1,600 req/s at 100% CPU; at 80% that's 1,280 req/s. **The two agree — the pool is correctly matched to the CPU budget.**

**Virtual threads:** the thread count stops being the constraint — you can run one per request. But throughput does **not** rise to infinity. The ceiling moves to whichever comes first: the 1,600 req/s CPU limit, or the **downstream connection pool**. If the DB pool has 20 connections and each request holds one for 25 ms, that pool caps you at 20/0.025 = **800 req/s**, and everything above that just queues. The fix is a semaphore/bulkhead sized to the real downstream capacity, not more threads.

**Full marks:** states assumptions, does both calculations, and identifies that the bottleneck moves rather than disappears.

---

### F2. `[AVP]` Amdahl's Law and the parallelisation decision

*A nightly batch job takes **120 minutes**. Profiling shows **75%** of the wall time is a per-record transform that parallelises cleanly; the remaining 25% is sequential file I/O and a final ordered write.*

**a) Speedup on 8 cores? b) On 32 cores? c) Theoretical maximum? d) What do you actually do?*

**Answer.** Amdahl: `Speedup = 1 / ((1 − P) + P/N)` with `P = 0.75`.

| N | Calculation | Speedup | Runtime |
|---|---|---|---|
| 8 | 1 / (0.25 + 0.09375) | **2.91×** | 41.3 min |
| 32 | 1 / (0.25 + 0.0234) | **3.66×** | 32.8 min |
| ∞ | 1 / 0.25 | **4.00×** | 30 min |

**The insight:** going from 8 to 32 cores — 4× the hardware cost — buys 8.5 more minutes. You are 73% of the way to the theoretical ceiling at 8 cores. **Effort belongs in the 30-minute sequential tail**, not in more parallelism: overlap the I/O with the compute (pipeline instead of phases), use a buffered/async writer, or partition the input so the "sequential" write becomes N independent writes merged later.

**Follow-up:** Where does Amdahl mislead? *(Gustafson's Law — if you scale the **problem size** with the cores, the sequential fraction shrinks proportionally and scaling looks much better. Amdahl assumes fixed work.)*

---

### F3. `[AM]` Contention and lock cost

*A counter is incremented on every request. At **50,000 increments/sec**, compare: (a) `synchronized`, (b) `AtomicLong`, (c) `LongAdder`, (d) a thread-local counter summed on read. 16 threads on 16 cores.*

**Answer.**

| Approach | Mechanism | Behaviour at 16-thread contention |
|---|---|---|
| `synchronized` | Monitor; biased → thin → **inflated** to an OS mutex under contention | Context switches cost ~1–5 µs each. Throughput collapses; threads park and unpark. |
| `AtomicLong` | CAS retry loop on one cache line | No context switches, but the cache line ping-pongs between cores. Each failed CAS costs a coherence miss (~100+ ns). At 16 threads, retry rate is high; effective throughput plateaus. |
| `LongAdder` | Striped `Cell[]`, one per contending thread, padded (`@Contended`) to separate cache lines | Writes scale nearly linearly — each thread mostly owns its cache line. `sum()` is O(#cells) and not atomic. |
| `ThreadLocal` + aggregate | Zero sharing | Fastest writes; read is a scatter-gather and needs a registry of threads to be correct. |

**The number to reach for:** 50,000/s across 16 threads is ~3,125/s per thread — **one increment every 320 µs**. That is *nowhere near* contended. All four options are fine; `AtomicLong` is the right default and `LongAdder` is premature. Contention only matters when the interval between increments approaches the cache-coherence latency (~100 ns), i.e. millions of ops per second.

**Full marks for saying the measurement makes the optimisation unnecessary.** This question rewards candidates who compute before optimising.

---

### F4. `[AVP]` Find the deadlock, prove it, fix it three ways

```java
void transfer(Account from, Account to, BigDecimal amt) {
    synchronized (from) {
        synchronized (to) {
            from.debit(amt);
            to.credit(amt);
        }
    }
}
```

**Answer.** All four Coffman conditions hold: mutual exclusion, hold-and-wait, no preemption, and **circular wait**. Thread 1 calling `transfer(A, B)` holds A and wants B; Thread 2 calling `transfer(B, A)` holds B and wants A.

**Probability intuition:** the window is only the few nanoseconds between acquiring the first and second lock — so this passes every test run and deadlocks in production at 3 a.m. under load. That's the point to make.

**Three fixes:**
1. **Global lock ordering** — always lock the lower ID first. Handle the equal-ID case (self-transfer) and hash collisions with a tie-breaker lock.
   ```java
   Account first  = from.id() < to.id() ? from : to;
   Account second = from.id() < to.id() ? to   : from;
   ```
2. **`tryLock` with timeout and backoff** — `ReentrantLock.tryLock(50, MILLISECONDS)`; on failure release everything, jitter, retry. Converts deadlock into a bounded, observable retry.
3. **Eliminate the lock** — make it a single atomic operation: one DB transaction with `SELECT ... FOR UPDATE` in a deterministic order, or an append-only ledger where the balance is a projection and there's nothing to mutate.

**Follow-up:** How would you *detect* it in production? *(Thread dump — the JVM literally prints "Found one Java-level deadlock" for monitor cycles. `ThreadMXBean.findDeadlockedThreads()` on a monitoring thread. Note it can't detect deadlocks via `ReentrantLock` in all cases, nor livelock or thread-pool starvation deadlock.)*

---

## Section G — Collections: Logic & Math *(7 min, pick 1)*

### G1. `[BOTH]` Resize cost

*You insert **1,000,000** entries into `new HashMap<>()` (default capacity 16, load factor 0.75). How many resizes happen, and roughly how much wasted work? What's the fix, and what capacity do you pass?*

**Answer.**

Capacity doubles when `size > capacity × 0.75`. Sequence: 16 → 32 → 64 → … The final capacity must satisfy `capacity × 0.75 ≥ 1,000,000`, so `capacity ≥ 1,333,334` → the next power of two is **2,097,152 (2²¹)**.

```
Resizes = log2(2,097,152 / 16) = 21 − 4 = 17 resizes
```

Each resize rehashes every entry present at that moment. Total entries moved ≈ sum of the thresholds ≈ `12 + 24 + 48 + … + 786,432` ≈ **1.57 million node relocations** — plus 17 array allocations totalling ~4.2 million slots, all of which becomes garbage.

**Fix:** pre-size. But note the trap — `new HashMap<>(1_000_000)` still resizes once, because the threshold is 750,000. You must divide by the load factor:
```java
new HashMap<>((int)(1_000_000 / 0.75f) + 1);   // → capacity 2,097,152, zero resizes
// or, Java 19+:
HashMap.newHashMap(1_000_000);
```

**Follow-up:** What if all 1M keys had the same `hashCode()`? *(Every entry lands in one bin. It treeifies to a red-black tree, so lookups are O(log n) ≈ 20 comparisons instead of 500,000 — but only if the key implements `Comparable`; otherwise it falls back to a tie-breaker on identity hash. Either way, throughput is destroyed and it's a known DoS vector.)*

---

### G2. `[AM]` Complexity arithmetic that changes a design

*Two lists of 100,000 strings each. You must find the intersection. Compare `list.contains()` in a nested loop vs. a `HashSet`. Put real numbers on it.*

**Answer.**

**Nested loops:** `ArrayList.contains` is O(n). Total comparisons = 100,000 × 100,000 = **10¹⁰**. At an optimistic 5 ns per string comparison (short strings, early mismatch):
```
10^10 × 5 ns = 50 seconds
```
Realistically minutes, because comparisons of similar strings are far slower.

**HashSet:** build the set in O(n), then n lookups at O(1):
```
200,000 operations × ~50 ns (hash + probe + equals) ≈ 10 ms
```

**~5,000× faster.** Memory cost: ~100,000 `HashMap.Node` objects at 32 bytes = 3.2 MB, plus a 262,144-slot table (~1 MB). Trading **4 MB for 50 seconds** is not a close call.

**Follow-up questions:**
- What if the lists are sorted? *(Merge-join with two pointers: O(n) time, O(1) extra space — beats the HashSet on memory and cache locality.)*
- What if one list is 100 million entries and won't fit in memory? *(External sort + merge, or a Bloom filter as a cheap pre-filter — ~1.2 MB for 1% false positives on 1M items — then verify hits against the real source.)*

---

### G3. `[AVP]` Pick the structure, defend the choice

*Design the data structure for an order book: **~500,000** live orders, keyed by price level. Operations: insert, cancel by order ID, and "give me the best 10 bids and asks" — thousands of times per second, on the hot path.*

**Answer.** No single structure does it; expect a **composite**.

- Price levels: **`TreeMap<Long, PriceLevel>`** (price in integer ticks, never `double`) or a **skip list / array of price buckets**. `firstKey()` / `headMap()` gives the top of book in O(log n), and a descending map for bids. If the price range is bounded and dense, an **array indexed by tick offset** turns O(log n) into O(1) with perfect cache locality — the standard choice in low-latency venues.
- Within a level: an **intrusive doubly-linked list** for FIFO time priority — O(1) append and O(1) removal *given the node*.
- Cancel by ID: **`HashMap<OrderId, OrderNode>`** holding a direct reference to the list node. This is what makes cancel O(1) instead of a scan. In practice, a primitive `long→object` open-addressing map to avoid boxing 500k IDs.
- Top-of-book: cache the best bid/ask; only recompute when the touched level empties or a better price arrives — turning thousands of reads per second into near-zero work.

**Cost check:** 500,000 orders × (order object ~48 B + node ~32 B + map entry ~32 B) ≈ **56 MB**. Fine on-heap, but it is 500k live objects for the GC to trace — a real argument for object pooling or off-heap flyweights in a latency-sensitive path.

**Full marks:** integer prices, O(1) cancel via the ID map, cached top-of-book, and a comment on GC pressure.

---

### G4. `[AM]` Reason about iteration order and stability

*Predict the output and explain each. Then say which are safe to rely on.*

```java
Map<String,Integer> a = new HashMap<>();
a.put("banana",1); a.put("apple",2); a.put("cherry",3);

Map<String,Integer> b = new LinkedHashMap<>(16, 0.75f, true); // access-order
b.put("x",1); b.put("y",2); b.put("z",3); b.get("x");

Set<Integer> c = new HashSet<>();
c.add(3); c.add(1); c.add(2);
```

**Answer.**
- **`a`** — unspecified order, determined by `hash & (capacity-1)`. It *looks* stable across runs for `String` (String's `hashCode` is deterministic), which is exactly the trap: code accidentally depends on it, then breaks when a key is added and the map resizes. **Never rely on it.**
- **`b`** — access-order LinkedHashMap. After `get("x")`, iteration yields `y, z, x` — the accessed entry moves to the tail. This is the 5-line LRU cache: override `removeEldestEntry` to return `size() > capacity`. Note `get()` is a *structural* modification here, so concurrent reads need external synchronisation and it will throw `ConcurrentModificationException` even from two "reading" threads.
- **`c`** — prints `1, 2, 3`. Not because `HashSet` is sorted, but because small `Integer` hashes equal their value and land in ascending buckets. Add `17` to a 16-slot table and the illusion collapses. Candidates who answer "HashSet is sorted" have a wrong mental model worth probing.

**Safe to rely on:** `LinkedHashMap`/`LinkedHashSet` (insertion or access order), `TreeMap`/`TreeSet` (comparator order), `List` (index order), `ArrayDeque` (FIFO/LIFO). **Everything else: no.**

---

## Section H — Memory Burn & CPU Cycles *(8 min, pick 1)*

> These are estimation questions. Give the candidate the reference card below; grade the reasoning chain.

**Reference card (HotSpot, 64-bit, compressed oops, heap < 32 GB):**

| Item | Size |
|---|---|
| Object header | 12 B (padded to 8-byte boundary) |
| Array header | 16 B |
| Reference | 4 B |
| `Integer` | 16 B · `Long`/`Double` 24 B |
| `HashMap.Node` | 32 B |
| `LinkedList.Node` | 24 B |
| `String` (n ASCII chars) | ~24 B + (16 + n) B, padded |
| L1 hit | ~1 ns (~4 cycles) |
| L3 hit | ~12 ns (~40 cycles) |
| Main memory | ~100 ns (~300 cycles) |
| Cache line | 64 B (= 16 `int`s) |
| 3 GHz core | 3 cycles/ns |

---

### H1. `[BOTH]` Memory footprint: boxing is not free

*You cache 5,000,000 `(long accountId → double balance)` pairs. Compare `HashMap<Long,Double>` against a primitive `long→double` open-addressing map. Show your working.*

**Answer.**

**`HashMap<Long, Double>`:**
| Component | Calculation | Size |
|---|---|---|
| Nodes | 5,000,000 × 32 B | 160 MB |
| Table array | capacity = next pow2 ≥ 5M/0.75 = 6.67M → **8,388,608**; 16 B + 4 B × 8.39M | 33.6 MB |
| `Long` keys | 5,000,000 × 24 B (outside the −128…127 cache) | 120 MB |
| `Double` values | 5,000,000 × 24 B (**never** cached — no autobox cache for `Double`) | 120 MB |
| **Total** | | **≈ 434 MB** |

**Primitive open-addressing map** (parallel `long[]` + `double[]`, ~50% load factor → 8,388,608 slots each):
```
8,388,608 × 8 B × 2 arrays ≈ 134 MB
```

**Result: ~3.2× less memory — and the more important number is object count.** The boxed version creates **15 million extra live objects** for the GC to trace on every marking cycle. The primitive version adds **two**. On a concurrent collector, live-set size and object count drive mark time directly; this is often a bigger win than the megabytes.

**Follow-up:** Where does the raw data actually sit? *(5M × 16 B of real payload = 80 MB. The boxed map is **5.4× overhead**. Ask what that means for a 512 MB container limit.)*

---

### H2. `[AVP]` Allocation rate, GC cadence, and promotion

*A service handles **3,000 req/s**. Each request allocates roughly **80 KB** (DTOs, JSON buffers, strings). Heap: **4 GB**, Eden **1 GB**, Old gen **2.5 GB**. Measured: minor GC pause **25 ms**; about **3%** of each young collection survives to Old.*

*Calculate: (a) allocation rate, (b) minor GC frequency, (c) GC overhead %, (d) promotion rate and time to fill Old, (e) is this healthy?*

**Answer.**

**(a) Allocation rate**
```
3,000 req/s × 80 KB = 240,000 KB/s ≈ 234 MB/s
```

**(b) Minor GC frequency** — Eden fills at the allocation rate:
```
1,024 MB ÷ 234 MB/s ≈ 4.4 s between minor GCs
```

**(c) GC overhead**
```
25 ms pause per 4.4 s cycle = 0.025 / 4.4 ≈ 0.57%
```
Comfortable. Under ~2–3% is generally fine; over 10% means the JVM is spending real capacity on GC.

**(d) Promotion rate**
```
234 MB/s × 3% ≈ 7 MB/s promoted
2,560 MB ÷ 7 MB/s ≈ 366 s ≈ 6.1 minutes to fill Old
```
So a concurrent old-gen cycle roughly every **6 minutes** — and if a G1 mixed collection or a full GC there costs 400 ms, that's the real p99.9 story, not the 25 ms minor pause.

**(e) Verdict.** Throughput impact is fine; the concern is the **6-minute old-gen cycle** and what happens if the survival rate rises. Levers, in order:
1. **Reduce allocation** — 80 KB per request is large. Stream JSON instead of materialising, reuse buffers, avoid intermediate collections. Halving it doubles the time between every GC of both generations.
2. **Grow Eden** — more short-lived objects die before promotion; halves promotion as well as frequency.
3. **Check survivor sizing / tenuring threshold** — 3% surviving may mean objects are being promoted prematurely because survivor spaces overflow. Watch for a cache or a leak, which shows as a *rising* survival rate over time.
4. Only then consider a different collector.

**Diagnostic to name:** GC logs (`-Xlog:gc*`), plotting allocation rate and promotion rate over time. A flat allocation rate with a climbing promotion rate is a leak.

---

### H3. `[AVP]` CPU cycle budget

*You need **p99 ≤ 10 ms** on a 3 GHz core. Your request does: 1 DB round trip (**4 ms**), 1 downstream HTTP call (**3 ms**), JSON deserialise + serialise of a 50 KB payload, and a business-rule pass over 200 items.*

*(a) What's the CPU budget? (b) Convert it to cycles. (c) Is JSON affordable? (d) Where's the risk?*

**Answer.**

**(a) Budget**
```
10 ms − 4 ms (DB) − 3 ms (HTTP) = 3 ms of CPU + queueing + GC
```
That 3 ms is not all yours: reserve ~1 ms for scheduling, TLS, framework overhead, and the chance of a GC pause landing inside the request. **Realistic compute budget: ~2 ms.**

**(b) Cycles**
```
2 ms × 3 GHz = 6,000,000 cycles
```

**(c) Affordability.** Jackson processes roughly 100–300 MB/s per core. For 50 KB in and 50 KB out:
```
100 KB ÷ 200 MB/s ≈ 0.5 ms  →  ~1,500,000 cycles
```
That is **25% of the entire budget on serialisation.** Affordable, but it's the single largest CPU item — and it's the first thing to attack (binary format, partial parsing, or not shipping 50 KB).

The 200 business rules: at ~200 ns each (branchy, some pointer chasing) that's 40 µs ≈ 120,000 cycles — **2% of budget, effectively free.** Optimising the rules would be wasted effort.

**(d) The real risk.** Not the CPU — it's the **variance**. The two network calls have their own tails; if the DB's p99 is 4 ms but its p99.9 is 40 ms, your p99 is fine and your p99.9 is blown. Add a 25 ms GC pause landing at random and you exceed 10 ms whenever it coincides with a request. **Tail latency compounds; averages don't.** Controls: bound the downstream with timeouts *below* your own budget, hedge requests, and shrink GC pauses (ZGC) if pauses are the dominant term.

---

### H4. `[AM]` Cache locality: why the "same" loop differs by 15×

*Both loops sum 10,000,000 values. Estimate the time difference and explain it.*

```java
int[] arr = new int[10_000_000];                 // A
List<Integer> list = new ArrayList<>(10_000_000); // B
```

**Answer.**

**A — `int[]`:** 10M × 4 B = **40 MB**, contiguous. The prefetcher walks it sequentially, and each 64 B cache line holds 16 ints.
```
Cache misses = 40 MB ÷ 64 B = 655,360
Memory stall = 655,360 × 100 ns ≈ 66 ms
```
Add ~1–2 cycles per element of actual work (~5 ms) and the prefetcher hides most of the stall. **Realistically ~10–20 ms**, largely bandwidth-bound.

**B — `ArrayList<Integer>`:** the array holds 10M **references** (40 MB), and each points to a separate 16 B `Integer` object somewhere else on the heap — another 160 MB. **200 MB total, 5× the footprint.** Every element is a pointer dereference to a location the prefetcher cannot predict, so it's ~1 miss per element:
```
10,000,000 × 100 ns ≈ 1,000 ms
```
Boxes allocated together may be adjacent and help somewhat, but after GC compaction and interleaved allocation, locality degrades. **Realistically 300 ms – 1 s.**

**Difference: roughly 15–50×, from a data-layout choice, not an algorithm change.** Same O(n).

**Follow-ups worth 30 seconds each:**
- *Would a parallel stream fix B?* Barely — it's memory-latency-bound, not CPU-bound. You'd add threads that all stall on memory.
- *False sharing:* two threads writing to `counters[0]` and `counters[1]` in an `int[]` share one cache line. Every write invalidates the other core's copy — a "lock-free" design that performs worse than a lock. Fix: pad to 64 B or use `@Contended`.
- *Array-of-structs vs. struct-of-arrays:* if you only sum one field of 10M objects, holding that field in its own `double[]` reads 8 B per element instead of pulling a whole 64 B object into cache.

---

## Appendix — Interviewer notes

**Running the hour:** Announce the section and time budget before each question. Interrupt at time; a partial answer scored honestly is more useful than a complete one that ate the next section.

**Choosing the set:**
- *AVP candidate:* A2 or A4 · B2 · C1 or C4 · D2 or D4 · E2 · F2 or F4 · G3 · H2 or H3
- *Assistant Manager candidate:* A1 or A3 · B1 · C2 or C3 · D1 or D3 · E1 or E3 · F1 · G1 or G2 · H1 or H4

**Signals that outrank correct answers:**
- Asks what the constraint is before proposing a solution.
- States assumptions out loud and revises them when challenged.
- Gives a number with an order of magnitude rather than "it depends".
- Says "I don't know, here's how I'd find out" instead of bluffing.

**Signals to discount:** naming tools without mechanisms; "we used Kafka for scalability"; reciting CAP; optimising something they never measured.
