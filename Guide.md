# AI/ML Modelling Engineer — 1-Hour Live Interview Guide (Detailed Answer Key)

A balanced, all-round panel covering ML fundamentals & statistics, model optimization & tuning, data/feature engineering, evaluation, GenAI, and critical thinking. Designed to **fit 60 minutes**, with backup questions if a section runs short. Each question now carries a **full model answer** — what a strong candidate should cover and *why* — plus red flags and good follow-up probes.

**How to use it:** Ask the core question, let the candidate talk for ~2 minutes, then push with a follow-up. The model answer is your reference for judging depth even if you're not a specialist in that sub-area. You're listening for *reasoning and tradeoffs*, not exact wording.

---

## Time Budget (60 min)

| Block | Topic | Time |
|---|---|---|
| 0 | Warm-up / resume probe | 5 min |
| 1 | ML fundamentals & statistics | 10 min |
| 2 | Model optimization & hyperparameter tuning | 12 min |
| 3 | Data, features & leakage | 10 min |
| 4 | Evaluation & metrics | 8 min |
| 5 | How ML / GenAI models actually work | 8 min |
| 6 | Critical thinking / logical reasoning | 5 min |
| 7 | Candidate's questions | 2 min |

Pick **one or two** questions per block. Depth beats coverage.

---

## Block 0 — Warm-up / Resume Probe (5 min)

**Q0.** Pick one model you built end-to-end and walk me through it: the problem, why you chose that algorithm, how you validated it, and one thing you'd do differently now.

**Model answer (what good looks like):**
A strong candidate frames the *business* problem first ("we needed to flag suspicious transactions while keeping analyst workload manageable"), not the algorithm. They then justify the algorithm against at least one alternative — e.g. "I used gradient boosting over logistic regression because the relationships were non-linear and we had strong tabular features, but I kept a logistic baseline for interpretability and as a sanity check." On validation, they should describe a concrete strategy appropriate to the data: a proper train/validation/test split, cross-validation, or — for any time-ordered data — a time-based or walk-forward split rather than a random one. Finally, the "what I'd do differently" answer reveals self-awareness: a good one might be "I'd version the training data and features from day one," or "I over-indexed on offline AUC and under-invested in drift monitoring."

**Red flag:** Can only describe library calls ("I called `RandomForestClassifier`"), can't articulate *why* the model suited the problem, or claims everything went perfectly. Inability to name a single tradeoff is the tell.

**Follow-up:** "If you had to ship that model with half the training data, what would you change?"

---

## Block 1 — ML Fundamentals & Statistics (10 min)

**Q1 (scenario-based bias–variance).** Read the candidate this concrete setup and have them diagnose it. Don't say the words "bias" or "variance" — let them get there.

> *"You've trained an XGBoost classifier to flag suspicious transactions. Config: `max_depth=12`, `n_estimators=900`, `learning_rate=0.2`, no regularization. Results: **training PR-AUC = 0.97, validation PR-AUC = 0.71.** You plot the learning curve (performance vs training-set size): the training curve sits flat and high near the top; the validation curve rises as you add data but is still climbing and hasn't plateaued, leaving a wide gap between the two. What's going on, and what would you do?"*

**Q1a — Diagnose it.** What does this pattern tell you?

**Model answer:**
This is a textbook **high-variance / overfitting** picture, and the candidate should read it off the evidence rather than guessing:
- The **large gap** between near-perfect training (0.97) and much weaker validation (0.71) means the model fits the training data far better than unseen data — it's memorizing noise, not learning generalizable signal.
- The **learning curve shape confirms it**: training stays high and flat while validation keeps *rising with more data* and hasn't converged. A still-climbing validation curve with a persistent gap is the signature of variance — more data is helping and would likely help further. (If both curves had converged low and close together, that would be *bias*, not variance — and the candidate should be able to contrast the two.)
- The **config explains the mechanism**: `max_depth=12` is very deep (thousands of leaves, highly specific decision paths), `learning_rate=0.2` with `n_estimators=900` is a lot of aggressive capacity, and **no regularization** removes the brakes. Together these give the model more than enough freedom to fit noise.

**Q1b — Fix it.** Give me three specific changes, and how you'd know each helped.

**Model answer:**
Strong candidates name *targeted* levers tied to the diagnosis, not a generic list:
1. **Reduce model capacity / add regularization** — drop `max_depth` to ~4–6, lower `learning_rate` (e.g. 0.03–0.05) with early stopping to choose `n_estimators`, and add `reg_lambda`/`reg_alpha`, raise `min_child_weight`, and use `subsample`/`colsample_bytree` < 1. Each directly shrinks the train–validation gap.
2. **Add more training data** — the still-rising validation curve says data is currently helping, so more should narrow the gap further (this is the rare case where "more data" genuinely is a fix, *because* the curve told us we're variance-limited).
3. **Prune the feature set / check for noisy or leaky features** — fewer, stronger features reduce the surface area for memorization; an oddly dominant feature might also signal leakage inflating the training score.

How you'd verify: after each change, **re-plot the learning curve and watch the gap.** A successful fix shrinks the train–validation gap and lifts validation PR-AUC *without* tanking training too far. If training drops to meet validation but both are now low (e.g. both ~0.70), you've over-corrected into the bias regime.

**Q1c — Flip it (tests the other side).** *"Now suppose instead the numbers were training PR-AUC = 0.69 and validation PR-AUC = 0.67, and the learning curves had converged close together and flat. Same fixes?"*

**Model answer:**
No — this is the **opposite problem: high bias / underfitting.** Both scores are low *and* close, and the curves have plateaued, so the model can't capture the signal and **more data won't help** (the curve has flattened). The correct moves are the reverse of Q1b: **increase** capacity (deeper trees, more rounds, less regularization), **engineer richer features**, or use a more expressive model. A candidate who reaches for "regularize / get more data" here has pattern-matched the words "improve the model" instead of reading the diagnostic — that's the distinction this question is built to expose.

**Red flag:** Treats every "bad model" as needing the same fix; can't read the gap and the learning-curve shape as distinct signals; says "add more data" in the Q1c (bias) case; or recites the bias–variance definition without mapping it onto the numbers in front of them.

**Follow-up if they're strong:** "In the original case, you lower `max_depth` and the gap closes but validation PR-AUC only reaches 0.78 and stops improving — where do you go next?" (You've moved from variance-limited toward the model's ceiling; further gains now come from *features* and data quality, not from more tuning of capacity.)

---

**Q2.** Random Forest vs gradient boosting (XGBoost/LightGBM) — explain the core mechanical difference, and when you'd reach for each.

**Model answer:**
Both are tree ensembles, but they combine trees in fundamentally different ways:

- **Random Forest = bagging (bootstrap aggregating).** It trains many *deep, independent* trees in parallel, each on a bootstrap sample of the rows and a random subset of features at each split. Predictions are averaged (regression) or voted (classification). Because the trees are decorrelated and averaged, RF primarily **reduces variance**. Individual trees overfit, but their errors cancel. It's robust, needs little tuning, handles mixed feature types, gives free out-of-bag error estimates, and is a great low-effort baseline.

- **Gradient boosting (XGBoost/LightGBM) = boosting.** It builds trees *sequentially*, where each new (usually shallow) tree fits the residual errors of the ensemble so far, via gradient descent in function space, with regularization. Because it keeps correcting its own mistakes, boosting primarily **reduces bias** and typically achieves higher accuracy on structured/tabular data. The cost: it's more sensitive to hyperparameters (learning rate, depth, number of trees) and easier to overfit if you don't tune or early-stop.

**When to use which:** Reach for RF as a fast, robust baseline when you want reliable results with minimal tuning, or when you need stability. Reach for boosting when you can invest in tuning and want maximum predictive performance, especially on tabular data. In a regulated context, both support feature importance and SHAP, so explainability isn't usually the deciding factor — tuning budget and stability are.

**Red flag:** Thinks "boosting is just a better forest," or can't say that bagging reduces variance while boosting reduces bias (different error components is the key insight).

**Follow-up:** "Why does boosting overfit more easily than RF?" (Each tree adapts to the current residuals, so noise gets fit if you add too many trees or set the learning rate too high — RF's independent averaging has no such feedback loop.)

---

**Backup Q1b (statistics).** What's the difference between a p-value and a confidence interval, and why might a "statistically significant" feature still be useless in a model?

**Model answer:**
A **p-value** is the probability of observing data at least as extreme as what you saw, *assuming the null hypothesis is true* — it's a statement about surprise under the null, not the probability the hypothesis is true. A **confidence interval** gives a range of plausible values for the effect at a given confidence level, so it conveys both direction and magnitude, which a bare p-value does not.

A feature can be "statistically significant" yet useless because:
- **Significance ≠ effect size.** With a large enough sample, a trivially small effect becomes significant. A coefficient can be significant and still move predictions negligibly.
- **Significance ≠ predictive value.** Statistical association in-sample doesn't guarantee out-of-sample lift, especially with multicollinearity (the feature's apparent significance may be borrowed from a correlated feature).
- **Multiple testing.** Test enough features and some clear the threshold by chance. Without correction (e.g. Bonferroni/FDR), "significant" features can be noise.

The strong candidate's punchline: significance answers "is there an effect?"; modeling cares about "does this feature improve generalization?" — different questions.

**Concrete example to make them apply it:**

> *"You're building a churn model on 2 million customers. You add a feature `days_since_last_app_open`. The logistic regression reports its coefficient as significant with **p < 0.001**, and the 95% confidence interval for the odds ratio is **[1.002, 1.004]**. A teammate says 'p is tiny, keep it — it's clearly important.' Do you agree?"*

**What a strong candidate says:** No — look at the interval, not just the p-value. The odds ratio of ~1.003 means each extra day shifts the odds of churn by about **0.3%**, and the CI is tightly bracketed *just above 1*, so the effect is real but **economically negligible**. The p-value is tiny only because n = 2M makes the standard error tiny — with two million rows, almost *any* non-zero effect becomes "significant." The right test is whether the feature **improves held-out predictive performance** (does validation PR-AUC / logloss actually move when you add it?), not whether p clears 0.05. They might also flag that if `days_since_last_app_open` is highly correlated with an existing engagement feature, its significance could be borrowed via multicollinearity and it adds nothing incremental.

**The trap this exposes:** a candidate who says "p < 0.001, definitely keep it" is reading significance as importance. The one who asks "significant, but how *big* is the effect, and does it lift the model out-of-sample?" understands the distinction.

---

## Block 2 — Model Optimization & Hyperparameter Tuning (12 min)

*The hardest-to-fake block — these are diagnostic scenarios, not definitions.*

**Q3 (early-stopping leakage).** A colleague tunes an XGBoost classifier like this and reports 94% "test accuracy":

```python
model.fit(X_train, y_train, eval_set=[(X_test, y_test)], early_stopping_rounds=20)
print(accuracy_score(y_test, model.predict(X_test)))   # reported as "test accuracy"
```

What's wrong, and how bad can it get?

**Model answer:**
The bug is subtle but serious: the *same* set (`X_test`) is used both as the early-stopping `eval_set` **and** as the reported test set. Early stopping watches performance on `eval_set` and halts when it stops improving — meaning it *selects* the number of boosting rounds (`n_estimators`/`best_iteration`) to maximize performance on exactly those rows. So `X_test` participated in model selection. The reported 94% is therefore **validation accuracy wearing a test-accuracy costume**: it's optimistically biased because the stopping point was chosen specifically to look good on those rows.

How bad it gets depends on how noisy the validation curve is. On large, clean datasets the inflation may be a fraction of a percent. On small, high-dimensional, or noisy data (e.g. text), it can inflate the reported metric by several points — enough to make a mediocre model look production-ready and fail on truly unseen data.

**The fix is a three-way split:** train on the training set, early-stop on a *separate validation set*, and report a single final number on a test set that was never touched during training or tuning. The deeper principle: early stopping *is* a hyperparameter search over `n_estimators`, and you never tune any hyperparameter on your test set.

**Red flag:** Sees nothing wrong, or argues "the test set is fine because the model never *trained* on it" — that misses that selecting where to stop is itself a form of fitting to that set.

**Follow-up:** "Is k-fold cross-validation with early stopping immune to this?" (Only if early stopping happens on an inner validation fold and the outer fold stays untouched — nested CV. Otherwise the same leakage reappears.)

---

**Q4 (the suspiciously tiny n_estimators).** You set `n_estimators=2000` with `early_stopping_rounds=50`. Training stops at round 73 with `best_iteration=23`, and the model loses to a logistic regression baseline. What are the most likely causes?

**Model answer:**
The model stopped almost immediately because validation loss plateaued after ~23 rounds — the trees aren't extracting usable signal beyond that point. Likely causes, roughly in order:

1. **Learning rate too high** (e.g. 0.3). Each tree takes a large step, so validation loss bounces around rather than descending smoothly, and the patience window (50 rounds with no improvement) trips early. Diagnostic: the eval curve looks *jagged*. Fix: lower the learning rate (e.g. 0.01–0.05) and allow more rounds.
2. **A leaked or dominant feature.** If one feature nearly determines the label, ~20 trees capture almost all the signal and everything after is noise. Diagnostic: check feature importances — one feature dominating overwhelmingly is suspicious. This *also* explains losing to a linear baseline only if the leak is weak/partial; more often a leak makes boosting look *too* good, so weigh this against the other symptoms.
3. **Eval-metric mismatch.** If you early-stop on `logloss` for a heavily imbalanced problem, loss can flatten while AUC is still improving — so you stop too early relative to the metric you actually care about. Subtlety: with multiple metrics in `eval_metric`, XGBoost early-stops on the *last* one in the list, which people miss.
4. **Data too small or noisy** for boosting to beat a linear model at all — sometimes logistic regression genuinely is the right model, and the honest answer is "boosting isn't adding value here."

The unifying diagnostic move: **plot the validation curve.** A jagged bounce says lower the learning rate; an instant flatline says investigate the features and the metric.

**Red flag:** Just says "increase `n_estimators`" — not realizing early stopping already chose the number of rounds, so raising the ceiling changes nothing.

**Follow-up:** "Lowering the learning rate, what else must you change to keep training effective?" (Raise the round budget — low LR needs many more trees to converge.)

---

**Backup Q4b (the depth illusion).** A teammate says "XGBoost `max_depth=6` and LightGBM `num_leaves=64` are equivalent — 2⁶ = 64." But LightGBM overfits much harder. Why isn't the equivalence real?

**Model answer:**
The two parameters constrain *different things* because the libraries grow trees differently:

- **XGBoost `max_depth=6` grows level-wise (depth-first balanced).** Every leaf is at most 6 splits from the root. You *can* have up to 64 leaves, but no single decision path can be more specific than 6 conditions deep — the depth cap limits how finely any one region of feature space is carved.
- **LightGBM `num_leaves=64` grows leaf-wise (best-first).** It repeatedly splits whichever leaf yields the maximum loss reduction, regardless of depth. The result is *lopsided* trees: one branch might go 20+ splits deep chasing a noisy pocket of the data while other branches stay shallow. With 64 leaves available and no depth limit, it can build very deep, very specific paths that memorize noise.

So `2⁶ = 64` equates the *leaf count* but ignores that LightGBM's leaf-wise growth produces far deeper, more specialized paths than XGBoost's depth-capped trees — which is exactly why LightGBM overfits harder at the "same" capacity. The fix is to also cap LightGBM's `max_depth` and/or raise `min_data_in_leaf` to rein in those deep noisy branches.

**Red flag:** Accepts the 2⁶ = 64 equivalence at face value, or doesn't know level-wise vs leaf-wise growth.

---

## Block 3 — Data, Features & Leakage (10 min)

**Q5 (leakage).** Give me a concrete example of data leakage you've caught or could imagine, and how you'd detect it before it ships.

**Model answer:**
Leakage is when information that wouldn't be available at prediction time (or is derived from the target) sneaks into training, producing models that look excellent offline and collapse in production. Concrete forms:

- **Temporal leakage:** a feature only known *after* the label event. E.g. "date account was closed" predicting churn, or "investigation outcome" predicting whether a transaction is suspicious — both are populated only after the thing you're predicting has happened.
- **Target-derived features:** aggregates computed using the label, or using future rows. E.g. encoding a category by its mean target value *before* splitting, so test rows' targets leak into training-time encodings.
- **Preprocessing leakage:** fitting scalers, imputers, or feature selection on the *full* dataset before the train/test split, so test statistics bleed into training.

**Detection / prevention:**
- Suspiciously high offline performance (near-perfect AUC) is the classic smell — investigate before celebrating.
- Inspect feature importances: a single feature dominating overwhelmingly often signals a leak.
- Fit *all* transformations (scaling, imputation, encoding, selection) **inside cross-validation folds** via a pipeline, never on the whole dataset.
- For time-ordered data, use a strict time-based split and ask of every feature: "would this value actually be known at prediction time?"

**Red flag:** Defines leakage abstractly but can't produce a realistic example, or fits preprocessing before the split.

**Follow-up:** "How would target encoding leak, and how do you do it safely?" (Compute encodings within CV folds / with out-of-fold schemes, never using a row's own target.)

---

**Q6 (imbalance).** Your positive class is ~1–5% of the data. How do you handle it, and what's the metric trap to avoid?

**Model answer:**
The trap is **accuracy**: a model that predicts "negative" for everything scores 95–99% accuracy while being useless. So first, change the metric — use **PR-AUC**, **recall@k**, or **F-beta** (with beta > 1 when missing positives is costlier than false alarms, e.g. F2). These focus on the minority class rather than being dominated by the easy majority.

Handling approaches, roughly in order of practical preference:
1. **Class weights** — e.g. `class_weight='balanced'` or `scale_pos_weight` in XGBoost — penalize minority errors more without touching the data. Usually the cleanest first move.
2. **Threshold tuning** — train normally, then choose the decision threshold from the precision–recall curve to hit your operational target (e.g. "recall ≥ 80% at the highest precision we can get"). Often the single highest-leverage lever.
3. **Resampling** — SMOTE/oversampling the minority or undersampling the majority. Critical caveat: apply resampling **only to the training folds, after the split** — resampling before splitting leaks synthetic neighbors across the boundary and inflates scores.

A strong candidate notes that in practice **class weights + threshold tuning often beat SMOTE**, and that the right operating point is a business decision (how many alerts can the downstream team actually action?).

**Concrete example to make them apply it:**

> *"You build a model to flag suspicious transactions. Out of 1,000,000 transactions, 2,000 are actually suspicious (0.2%). A colleague proudly reports the model is **99.8% accurate** and wants to ship it. On the held-out set the confusion matrix is: it flagged 50 transactions, of which 40 were truly suspicious; it missed 1,960 suspicious ones. Sign off, or not?"*

**What a strong candidate says:** Don't ship it. The 99.8% accuracy is an illusion — a model that flags *nothing at all* would already score 99.8% here, because 99.8% of transactions are legitimate. Compute the metrics that matter for the minority class:
- **Recall = 40 / 2,000 = 2%.** It catches almost none of the actual suspicious activity — the entire point of the system fails.
- **Precision = 40 / 50 = 80%.** When it does flag, it's usually right, so the model isn't *random* — it's just tuned far too conservatively.

The diagnosis: precision is high but recall is catastrophic, which is the classic signature of a threshold set too high on an imbalanced problem. The fix here isn't more data or a new algorithm first — it's to **lower the decision threshold** (and/or apply class weights/`scale_pos_weight`) to trade some of that 80% precision for far more recall, then choose the operating point on the precision–recall curve against what the investigation team can handle. Report **PR-AUC and recall at a usable precision**, never accuracy.

**The trap this exposes:** a candidate who hears "99.8% accurate" and nods is anchored on the wrong metric. The one who immediately asks "what's the recall on the 0.2%?" understands that on imbalanced data, accuracy measures how well you predict the *boring majority*, not whether you solve the problem.

**Red flag:** "Just SMOTE it" with no mention of where in the pipeline it goes, or optimizes accuracy.

**Follow-up:** "Why is applying SMOTE before the train/test split wrong?" (Synthetic points are interpolated from real points; if a real point lands in train and its synthetic neighbor in test, the test set is contaminated.)

---

## Block 4 — Evaluation & Metrics (8 min)

**Q7 (PR vs ROC).** Why might you prefer a Precision–Recall curve over ROC-AUC on a highly imbalanced problem?

**Model answer:**
ROC plots True Positive Rate (recall) against False Positive Rate, where FPR = FP / (FP + TN). When negatives are 95–99%+ of the data, **TN is enormous**, so even thousands of false positives barely move FPR. The result is an inflated ROC-AUC — a model can look like 0.98 while flooding the downstream team with false alerts.

The Precision–Recall curve instead plots:
- **Precision = TP / (TP + FP)** — "of everything I flagged, how much is real?"
- **Recall = TP / (TP + FN)** — "of everything real, how much did I catch?"

Both are computed purely from the minority-class perspective and **neither is diluted by the huge true-negative count**, so PR-AUC reflects performance where it matters. The practical reporting pattern: PR-AUC as the headline, plus **recall at a fixed operational precision** (e.g. "what recall do we get at 20% precision — i.e. 1 in 5 alerts being real?"), because that's the number the people consuming the alerts actually feel.

**Red flag:** Treats ROC-AUC as the universal metric, or can't explain *why* the large TN count distorts it.

**Follow-up:** "Two models have the same PR-AUC but different curve shapes — how do you choose?" (Pick based on the region of the curve you'll actually operate in — high-recall vs high-precision end — not the aggregate area.)

---

**Q8 (threshold = business decision).** Your model has F1 = 0.85 (precision 0.80, recall 0.90). The intervention triggered by a positive prediction is *expensive*. What do you change — and is this a modeling change or a business one?

**Model answer:**
An expensive intervention means **false positives are costly**, so you want to favor **precision** over recall. The right move is **not to retrain** — it's to **raise the decision threshold** so you only act on higher-confidence positives, trading some recall for precision. You choose the new threshold from the precision–recall curve by weighing the cost of a wrong intervention against the value of a correct one.

The key insight a strong candidate articulates: **this is a business decision, not a modeling one.** F1 weights precision and recall equally, but the real cost structure here is asymmetric, so F1 is the wrong objective to optimize blindly. The model's *ranking* of cases can be perfectly good; what changes is where you draw the line based on economics. Retraining, gathering more data, or swapping algorithms are all over-engineered responses to what is fundamentally a thresholding choice.

**Red flag:** Jumps to "retrain" or "collect more data" instead of recognizing threshold tuning, or doesn't connect the threshold to cost.

**Follow-up:** "When *would* moving the threshold not be enough, forcing you to actually change the model?" (When even at the precision you need, recall is unacceptably low — the model's ranking itself is too weak, so you need better features or a better model.)

---

## Block 5 — How ML / GenAI Models Actually Work (8 min)

**Q9 (LLM fundamentals).** In plain terms, how does a transformer-based LLM generate text, and why does it "hallucinate"?

**Model answer:**
An LLM generates text **autoregressively**: given the tokens so far, it predicts a probability distribution over the next token, samples or picks from it, appends it, and repeats. The **transformer** architecture uses *self-attention*, which lets each position weigh the relevance of every other token in the context when forming its representation — that's what lets the model use long-range context rather than just the previous word. It's trained on massive text to minimize next-token prediction error.

Hallucination follows directly from the objective: the model is optimized to produce *plausible, fluent continuations*, **not true ones**. It has no built-in notion of truth, no grounding in an external source of facts, and no verification step — so when it lacks the knowledge, it generates the most statistically likely-sounding text, which can be confidently wrong. Hallucination is therefore an expected property of the mechanism, not a fixable "bug." Mitigations work by adding what the model lacks: **retrieval grounding (RAG)** to supply real source documents, constrained decoding, tool use, and downstream verification.

**Red flag:** Treats the model as a database/lookup, or thinks hallucination is a bug that a bigger model simply eliminates.

**Follow-up:** "Why doesn't lowering the sampling temperature to zero stop hallucinations?" (Greedy decoding only removes randomness; if the most probable continuation is itself wrong, the model still confidently produces falsehoods.)

---

**Q10 (RAG vs fine-tuning, and when GenAI is the wrong tool).** When would you use a RAG system over fine-tuning, and when is an LLM the *wrong* tool entirely?

**Model answer:**
**RAG (retrieval-augmented generation)** retrieves relevant documents at query time and feeds them into the prompt, so the model answers *from* that supplied context. Use it when the knowledge is **changing, proprietary, or large**, and when you need **freshness and citations** — you can update the knowledge base without retraining, and you can show sources, which matters in regulated settings.

**Fine-tuning** adjusts the model's weights on examples. Use it to change **behavior, format, tone, or domain reasoning** — teaching the model *how* to respond — rather than to inject facts. Fine-tuning is a poor and expensive way to keep a model "up to date" on facts; RAG is better for that.

An LLM is the **wrong tool entirely** when you need deterministic, auditable, low-latency numeric decisions — e.g. credit or transaction scoring where you must justify every decision to a regulator and reproduce it exactly. There, a **calibrated tabular model** (gradient-boosted trees with SHAP explanations) is more accurate on structured data, far cheaper, faster, reproducible, and defensible. The strongest candidates volunteer this: knowing when *not* to use GenAI is as important as knowing how to use it.

**Red flag:** "Use an LLM for everything," conflates RAG with fine-tuning, or can't name a case where classical ML clearly wins.

**Follow-up:** "Your RAG system gives a wrong answer. How do you tell whether retrieval or generation failed?" (Inspect the retrieved chunks: if the right document wasn't retrieved, it's a retrieval/embedding/chunking problem; if the right context was present but the answer ignored it, it's a generation/prompting problem.)

---

**Q11 (lexical retrieval — BM25 & friends).** Before vector embeddings, retrieval ran on algorithms like TF-IDF and BM25. Explain what BM25 actually does, and — given that we have dense embeddings now — why would you still use it in a modern RAG/search system?

**Model answer:**
BM25 is a **lexical (keyword) ranking function** — it scores how well a document matches a query based on the *actual words they share*, not on meaning. It builds on **TF-IDF** and refines it with two ideas:
- **Term frequency with saturation:** a query word appearing more often in a document raises the score, but with *diminishing returns* — going from 1 to 5 occurrences matters a lot, 50 to 55 barely moves it. (Plain TF-IDF has no saturation, so it over-rewards keyword stuffing; BM25's `k1` parameter controls this.)
- **Inverse document frequency:** rare words (e.g. a specific account ID or "structuring") count for more than common ones ("the", "transaction"), because matching a rare term is far more informative.
- **Document-length normalization** (the `b` parameter): long documents naturally contain more words, so BM25 discounts them to avoid unfairly favoring long docs that match by sheer size.

The crucial distinction: BM25 is **sparse/lexical** — it matches surface tokens and knows nothing about semantics, so "car" and "automobile" are unrelated to it. Dense embeddings are **semantic** — they capture meaning, so paraphrases and synonyms match, but they can miss *exact* terms.

**Why still use it:** because the two fail in opposite ways, and the strong answer is that you usually want **both** (hybrid search):
- BM25 is unbeatable at **exact-match / rare-token** retrieval — specific IDs, error codes, names, regulation numbers, ticker symbols. Embeddings often blur these because the exact string isn't "semantically distinctive."
- It needs **no training, no GPU, no embedding model**; it's fast, cheap, fully interpretable (you can see exactly which terms drove the score), and works out-of-the-box on a new domain with zero data.
- It's a strong **baseline and a safety net** — many teams find a BM25 baseline is surprisingly hard to beat, and a **hybrid** approach (combine BM25 and dense scores, e.g. via reciprocal rank fusion) reliably beats either alone: dense recall for paraphrases, BM25 precision for exact terms.

**Red flag:** Thinks vector search has made BM25 obsolete; can't explain *why* keyword search still wins on exact-match/rare-term queries; or has never heard of hybrid retrieval and assumes "embeddings are just better."

**Follow-up:** "A user searches your AML knowledge base for a specific regulation code like 'BSA 314(b)' and the dense-only retriever returns vaguely related compliance docs but not the exact one. Why, and what fixes it?" (The embedding smooths the rare alphanumeric token into a generic 'compliance' region of vector space; BM25 would match the literal token exactly — add a lexical/hybrid leg to the retriever.)

---

## Block 6 — Critical Thinking / Logical Reasoning (5 min)

*Pick one. You're testing reasoning under ambiguity, not a single "right answer."*

**Q12 (production degradation).** A model that ran fine for 6 months suddenly degrades in production, but the offline AUC on your held-out set is still great. Walk me through how you'd diagnose it.

**Model answer:**
The fact that offline metrics are still good but production isn't points away from "the model got worse" and toward "the world or the pipeline changed." A structured candidate separates the hypotheses and names a detection method for each:

- **Data drift (covariate shift):** the input distribution moved (new customer mix, new product). Detect with **PSI or KS tests** comparing recent feature distributions to the training distribution.
- **Concept drift:** the *relationship* between features and label changed (a pricing change, a new competitor, a new laundering technique). Detect via **rolling performance on freshly labelled data** once labels arrive.
- **Training/serving skew:** features are computed differently in the training pipeline vs the serving path (a unit, default, or timezone mismatch). Detect by **logging the features actually served and comparing them to training-time features** for the same entities.
- **Upstream/pipeline breakage:** a data source changed schema, started delivering late, or began emitting nulls. Check the data-validation step and recent deploys.

The hallmark of a strong answer is being **hypothesis-driven and methodical** — forming distinct hypotheses and testing each — rather than immediately retraining. Retraining without diagnosis fixes nothing if the cause is serving skew or a broken upstream feed.

**Red flag:** Immediately blames the model and wants to retrain without investigating *why* it degraded.

**Follow-up:** "Offline AUC is good but production is bad — which of your hypotheses does that fact alone make *more* likely?" (Serving skew or upstream breakage, because those affect production inputs without touching your offline held-out set.)

---

**Q13 (estimation / Fermi reasoning).** Roughly how many ML inference calls per second would a system serving 10M users, each triggering ~20 scored events/day, need to handle at peak? Walk me through your assumptions.

**Model answer:**
What's being tested is *how they reason under uncertainty*, not the exact number. A good answer thinks out loud and states assumptions:

- Volume: 10M users × 20 events/day = **200M events/day**.
- Average rate: 200M ÷ 86,400 s ≈ **~2,300 calls/sec** averaged over 24 hours.
- Peak factor: traffic isn't uniform — assume peak is **3–5×** the average (business hours, time-zone concentration) → roughly **7,000–12,000 calls/sec at peak**.
- Design implications: at that rate you'd consider **batching** requests, **caching** scores for entities whose features haven't changed, **horizontal scaling** of stateless inference servers, and **asynchronous** scoring for events that don't need a real-time answer.

The quality signal is the *explicitness and reasonableness of the assumptions* and the willingness to refine them — not arithmetic precision.

**Red flag:** Either freezes without making any assumptions, or fires a single number with no reasoning to back it.

**Follow-up:** "Which of those assumptions, if wrong by 2×, changes your architecture the most?" (Usually the peak factor and whether scoring must be synchronous — those drive the capacity and latency design.)

---

## Block 7 — Candidate's Questions (2 min)

Leave room. The questions a strong candidate asks — about data quality, label availability, model governance, retraining cadence, and how success is measured — are themselves a signal of how they think about real systems.

---

## Quick Scoring Sheet

| Dimension | 1 (weak) | 3 (solid) | 5 (strong) |
|---|---|---|---|
| ML fundamentals | Memorized definitions only | Connects concepts to real work | Reasons about tradeoffs fluently |
| Tuning & optimization | Tunes knobs by trial-and-error | Knows what each knob does | Diagnoses problems from curves/symptoms |
| Data & leakage instinct | Misses leakage | Catches obvious cases | Designs pipelines to prevent it |
| Evaluation judgment | Defaults to accuracy/AUC | Picks the right metric | Ties metric choice to business cost |
| GenAI understanding | Treats the LLM as magic | Knows the mechanics | Knows when *not* to use it |
| Critical thinking | Jumps to conclusions | Structured approach | Hypothesis-driven under ambiguity |
| Communication | Jargon, unclear | Clear and organized | Teaches the interviewer something |

---

### Notes for the panel
- Ask the **same core question per block** to every candidate and vary only the backups — it makes comparison fairer.
- If you want a **harder variant** of any block (a Python coding round, a stats-heavy round, or a systems-design round), the source banks we built earlier have deeper pulls to draw from.
- These answers are reference *ceilings*, not scripts — a candidate phrasing the same reasoning differently should still score well.
