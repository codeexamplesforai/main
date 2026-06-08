Build a small lazy, composable stream-processing (ETL) framework in pure standard-library Python. Requirements:

A @stage decorator that turns a generator function rows -> rows into a reusable, named Stage, and rejects any function that isn't a generator function (validate at decoration time). It must work both as @stage and as @stage(name="...").
Stage objects compose with the | operator: clean | dedupe returns a new Stage whose generator pipes the first into the second (use yield from).
A Pipeline(source) whose constructor takes any iterable; pipeline | stage | stage builds a chain that is fully lazy — nothing runs until you iterate it. Provide .collect().
A parametrized @retry(attempts, base_delay, exceptions) decorator with exponential backoff, used to wrap a flaky source fetch.
Provide stages: clean (strip/drop empties), dedupe, a batched(n) stage factory, and a tap(fn) stage for side effects.
Bonus / discussion: add a two-way generator driven by .send() and explain why .send()-style control does not naturally compose through a pull-based yield from pipeline.
