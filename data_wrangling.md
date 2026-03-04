# Module6_DataWranglingP1_Cleaning_Diary.md

## Data Cleaning Diary – Module 6 (Part 1)

### Overview

In this phase, I focused on making the dataset analytically reliable before moving into modeling and sentiment analysis. The goal was to eliminate structural noise, standardize formats, and ensure that the remaining comments represent meaningful, high-quality input data.

---

## Top Data Problems I Fixed First (and Why)

### 1. Missing and Empty Text Fields

**Why this first?**
Sentiment analysis depends entirely on textual input. Rows with missing or empty `text` or `video_description` fields are unusable for NLP tasks and would distort downstream statistics.

### Rule Applied:

* **Drop** rows where:

  * `video_description` is null
  * `text` is null
  * `video_description` or `text` is an empty string (after stripping whitespace)

This ensures that all retained rows contain meaningful content.

#### Before vs After (Structure Summary)

**Before cleaning:**

* Dataset loaded with full row count from `comments_data.csv`
* Included nulls and empty strings in key text columns

```python
data.isna().sum()
```

**After filtering:**

```python
filtered_data = data[
    data['video_description'].notna() &
    data['text'].notna()
]
```

Result:

* All remaining rows contain usable comment text
* Removed structurally invalid observations

This step reduced dataset size but increased analytical validity.

---

### 2. Datetime Inconsistency

**Why early?**
Time-based features are central to my project (event reactions, sentiment decay, comment latency). Incorrect datetime types would break temporal calculations.

### Rule Applied:

* **Convert** string columns to datetime:

  * `comment_date`
  * `video_date`
  * `last_updated_at`
* **Sort** dataset chronologically by `comment_date`

```python
data['comment_date'] = pd.to_datetime(data['comment_date'])
data = data.sort_values('comment_date').reset_index(drop=True)
```

This enabled:

* Event-relative day calculations
* Latency metrics
* Time-series analysis

---

### 3. Low-Quality and Non-English Comments

**Why this early?**
My sentiment model (RoBERTa) is English-based. Non-English text and very short comments (e.g., “lol”, “ok”) introduce noise and reduce signal clarity.

### Rule Applied:

* **Filter**:

  * `language == 'en'`
  * `word_count >= 3`
  * `text` not null

```python
data_clean = data[
    (data['language'] == 'en') &
    (data['word_count'] >= 3)
].copy()
```

This step prioritizes linguistic consistency and meaningful content.

---

### 4. Bot-like or Duplicate Comments

**Why important?**
Duplicate comments inflate frequency-based analysis and bias engagement statistics.

### Rule Applied:

* **Deduplicate** identical comment texts

```python
data_clean = data_clean.drop_duplicates(subset=['text'], keep='first')
```

This reduces artificial amplification and improves fairness in engagement-weighted sentiment scoring.

---

### 5. Text Normalization for NLP

**Why necessary?**
Transformer models are sensitive to noise like URLs and user mentions.

### Rule Applied:

* **Normalize**:

  * Replace URLs → `[URL]`
  * Replace @mentions → `[USER]`
  * Normalize whitespace

```python
text = re.sub(r'http\S+|www\S+', '[URL]', text)
text = re.sub(r'@\w+', '[USER]', text)
```

This preserves semantic meaning while reducing token noise.

---

## Remaining Risks

Even after cleaning, several risks remain:

### 1. Language Filtering Bias

Filtering to English-only:

* Removes potentially valid opinions
* Biases sentiment toward English-speaking users
* May underrepresent global player perspectives

### 2. Short Comment Removal

By enforcing `word_count >= 3`, I removed:

* Emotional but short reactions (“trash”, “amazing”)
* Highly polarized but concise feedback

This may dampen extreme sentiment representation.

### 3. Duplicate Removal Assumptions

Dropping identical text assumes:

* Repeated comments are bots or spam
  However:
* Some real users may independently write identical short reactions

This could slightly distort engagement frequency.

### 4. Engagement Skew

Like counts are highly skewed:

* A small fraction of comments drive most engagement
* Future weighting decisions could amplify popularity bias

---

## Reflection

This cleaning phase reinforced how critical structure is before analysis. It is easy to jump into modeling, but poor input quality would invalidate results. Removing nulls, enforcing language consistency, and deduplicating comments significantly improved reliability.

I also realized that every filtering choice implicitly affects fairness. Cleaning is not neutral—it shapes whose voices remain in the dataset.

---

## Next Steps

* Apply RoBERTa sentiment scoring
* Filter low-confidence predictions
* Construct popularity-weighted sentiment metrics
* Analyze sentiment trends around major announcements
* Compare pre- and post-event engagement clusters

---

# DataWranglingP2_FeatureEngineering_Diary.md

## Data Wrangling – Part 2: Feature Engineering Diary

### Overview

After cleaning the dataset, I engineered features designed to capture temporal context, event relevance, engagement intensity, and conversational structure. These features transform raw comments into analytically meaningful variables.

---

## Features Engineered (and Why)

### 1. Event Mention Detection

**Why?**
I wanted to identify comments directly responding to major announcements:

* GenAI voice announcement
* Business model change
* Game launch

### Implementation:

Binary keyword detection:

```python
data['mentions_genai'] = data['text'].apply(...)
data['mentions_business_model'] = data['text'].apply(...)
```

This allows:

* Isolating event-driven discourse
* Comparing sentiment between event-focused and general comments

---

### 2. Temporal Distance from Major Events

**Why?**
Sentiment often decays or intensifies over time after announcements.

### Implementation:

For each event:

```python
data['days_from_genai_announcement'] = (
    data['comment_date'] - event_date
).dt.days
```

This enables:

* Pre vs post-event comparison
* Sentiment decay modeling
* Time-relative regression analysis

---

### 3. Engagement Features

Engagement is central to weighted sentiment modeling.

#### Engineered:

* `has_likes` → Boolean engagement flag
* `like_count_log` → Log transform to reduce skew
* `engagement_tier` → Categorical binning
* `comment_latency_days` → Time between upload and comment
* `latency_category` → Binned latency class

Example transformation:

```python
data['like_count_log'] = np.log1p(data['likes'])
```

**Why log-transform?**
Like distributions are heavily right-skewed. Log scaling:

* Reduces dominance of viral comments
* Stabilizes variance for modeling

---

### 4. Conversational Context Features

To enrich context for future LLM analysis:

* `video_context` → First 500 characters of description
* `parent_text` → Mapped parent comment for replies

This allows:

* Thread-level sentiment analysis
* Conversation-aware modeling

---

## Feature Selection: What I Removed and Why

In the final dataset, I retained only analytically relevant columns:

```python
columns_to_keep = [
    'comment_id', 'parent_id', 'parent_text',
    'text', 'text_preprocessed',
    'video_context', 'video_id',
    'comment_date', 'author_hash',
    'days_from_genai_announcement',
    'days_from_business_model_change',
    'days_from_game_launch',
    'mentions_genai', 'mentions_business_model',
    'likes', 'like_count_log'
]
```

### Removed Columns

* Raw API metadata not relevant to modeling
* Redundant timestamp variants
* Unused auxiliary fields

### Justification:

* **Relevance**: Only features tied to sentiment, time, or engagement were retained.
* **Redundancy**: Derived fields replaced raw equivalents.
* **Ethics**: No personally identifiable information retained (only `author_hash`).

---

## Before vs After Example: Engagement Transformation

### Before:

* `likes` highly skewed
* Many zeros
* Few extreme high values

### After:

* `like_count_log` compresses scale
* Engagement tiers categorize intensity:

Example tier bins:

* `no_likes`
* `low_engagement`
* `medium_engagement`
* `high_engagement`
* `viral`

This makes modeling more stable and interpretable.

---

## Risks and Interpretation Considerations

### 1. Keyword-Based Event Detection

* May miss implicit references
* May falsely classify sarcasm or unrelated usage

### 2. Log Transformation Bias

Log scaling reduces dominance of viral comments, but:

* It also reduces the relative influence of genuinely important high-impact discourse.

### 3. Engagement Tiers

Bin thresholds are manually defined:

* Different bin cutoffs could change results
* This introduces researcher subjectivity

### 4. Temporal Framing

Using fixed event dates assumes:

* All audience members react immediately
  In reality:
* Exposure timing varies significantly

---

## Reflection

Feature engineering made the dataset analytically rich. Instead of just raw comments, I now have structured signals:

* Event alignment
* Engagement intensity
* Temporal positioning
* Conversational hierarchy

This stage shifted the project from simple text analysis to a structured modeling pipeline. It also made me more aware of how engineered features shape interpretation. Every transformation embeds assumptions.

---

## Next Steps

* Run RoBERTa sentiment scoring
* Filter predictions below 0.70 confidence
* Construct popularity-weighted sentiment
* Compare:

  * Event vs non-event comments
  * High vs low engagement tiers
  * Early vs late reaction patterns
* Model sentiment decay over time using event-relative features

---

# Module6_DataWranglingP1_Cleaning_Diary.md

## What were the top data problems I fixed first, and why?

The first issues I addressed were missing or empty text fields, inconsistent datetime formats, duplicate comments, and low-quality entries (very short or non-English comments). I prioritized these because sentiment analysis depends on valid text input and reliable timestamps. If the core text or time variables are broken, everything downstream (event analysis, sentiment trends, engagement timing) becomes unreliable.

I also noticed skew and noise in engagement-related fields, but I focused first on structural integrity (missing values, types, duplicates) before worrying about transformations. The goal was to make the dataset analytically stable before feature engineering.

---

## What rule did I apply to each problem (and why)?

* **Missing text fields** → *Drop*: Rows with null or empty `text` or `video_description` were removed because they are unusable for NLP.
* **Datetime columns** → *Convert*: I converted string timestamps to proper datetime format so I could compute time differences and sort chronologically.
* **Duplicate comments** → *Deduplicate*: I removed duplicate `text` entries to avoid inflated frequency or engagement signals.
* **Short / non-English comments** → *Filter (drop)*: I kept only English comments with at least three words to reduce noise and ensure compatibility with the sentiment model.
* **Noisy text (URLs, mentions)** → *Normalize*: I replaced URLs and @mentions to make the text cleaner for modeling.

These steps reduced dataset size but improved overall quality and consistency.

---

## Before vs After Summary

Before cleaning, the dataset contained missing text values, empty strings, and inconsistent timestamp formats. After dropping nulls and filtering for `word_count >= 3`, the dataset became smaller but more uniform. Missingness in key text columns was reduced to zero, and all datetime columns were properly typed, enabling event-based calculations.

Engagement values remained skewed, but structurally the dataset became fully usable for modeling.

---

## Remaining Risks and Fairness Considerations

Filtering to English introduces language bias and may exclude meaningful international perspectives. Removing short comments could eliminate strong but concise emotional reactions. Deduplicating identical text assumes repetition equals spam, which may not always be true.

Overall, cleaning improved reliability, but each filtering decision shapes representation and may affect how sentiment trends are interpreted later.

---

# DataWranglingP2_FeatureEngineering_Diary.md

## What features did I engineer (or transform), and why?

I engineered event-based features by creating binary flags for comments mentioning key announcements and calculating the number of days between each comment and major event dates. This allows me to compare pre- and post-event reactions and model sentiment decay over time.

I also transformed engagement-related features. Because like counts were highly skewed, I applied a log transformation (`log1p`) to stabilize variance. I created engagement tiers and a comment latency variable (days between upload and comment) to better understand reaction timing and popularity intensity.

These features turn raw comments into structured signals that are more useful for modeling and interpretation.

---

## What did I remove during feature selection, and why?

I removed unused metadata columns, redundant timestamp variants, and fields not directly relevant to sentiment, engagement, or timing. This was mainly for relevance and redundancy reasons — keeping unnecessary variables increases noise and complicates modeling.

I also avoided retaining personally identifiable information beyond anonymized hashes. This helps reduce ethical concerns while still allowing user-level grouping if needed.

---

## Before vs After Summary

Before transformation, like counts were extremely skewed with many zeros and a few very high values. After applying a log transformation, the distribution became more compressed and suitable for modeling.

Similarly, before feature engineering, the dataset only had raw timestamps. After adding event-relative day counts, I can now directly compare reactions before and after announcements, which was not possible in the raw dataset.

---

## Remaining Risks and Interpretation Concerns

Keyword-based event detection may miss indirect references or misclassify sarcasm. Log-transforming likes reduces skew but also reduces the relative influence of viral comments. Engagement tiers depend on chosen thresholds, which introduces subjectivity.

These decisions could affect fairness and interpretation later, especially when weighting sentiment by engagement or comparing event-driven versus general discourse.
