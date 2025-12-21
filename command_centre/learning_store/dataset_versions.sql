-- ============================================================================
-- Command Centre Learning Store: Dataset Versions Table
-- ============================================================================
--
-- PURPOSE:
--   Track dataset versions used for training to ensure reproducibility.
--
-- CRITICAL NOTES:
--   - Each training run should use a specific dataset version
--   - Versions capture the state of learning_samples + hitl_labels at a point in time
--   - Enables reproducible training and comparison across model versions
--   - Tracks which samples were included in which training runs
--
-- VERSIONING STRATEGY:
--   - Semantic versioning recommended: v1.0.0, v1.1.0, v2.0.0
--   - Each version is immutable once created
--   - New data = new version (don't modify existing versions)
--
-- DATA FLOW:
--   1. Accumulate samples and labels in learning store
--   2. Periodically create a new dataset version (snapshot)
--   3. Training pipeline reads specific version
--   4. Track which version produced which model
--   5. Can compare models trained on different versions
--
-- ============================================================================

CREATE TABLE IF NOT EXISTS dataset_versions (
    -- Primary key: Version identifier
    dataset_version TEXT PRIMARY KEY,

    -- Version metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),  -- When was this version created
    description TEXT,                                    -- Human-readable description

    -- Dataset composition
    total_samples INTEGER NOT NULL DEFAULT 0,            -- Total number of samples in this version
    total_labels INTEGER NOT NULL DEFAULT 0,             -- Total number of labels in this version
    samples_with_corrections INTEGER DEFAULT 0,          -- How many samples have 'changed' labels
    samples_confirmed_correct INTEGER DEFAULT 0,         -- How many samples have 'correct' labels
    samples_unsure INTEGER DEFAULT 0,                    -- How many samples have 'unsure' labels

    -- Data provenance
    source_cities TEXT,                                  -- Which cities contributed data (JSON array or CSV)
    date_range_start TEXT,                               -- Earliest sample timestamp in this version
    date_range_end TEXT,                                 -- Latest sample timestamp in this version

    -- Version characteristics
    is_production BOOLEAN DEFAULT FALSE,                 -- Is this the production dataset?
    is_archived BOOLEAN DEFAULT FALSE,                   -- Has this version been archived?

    -- Quality metrics
    average_confidence REAL,                             -- Average detection confidence in this version
    label_agreement_rate REAL,                           -- % of samples with operator agreement

    -- Usage tracking
    used_in_training_runs INTEGER DEFAULT 0,             -- How many training runs used this version
    last_used_at TEXT,                                   -- When was this version last used

    -- Additional metadata (JSON or text)
    metadata TEXT,                                       -- Additional version-specific metadata

    -- Notes and comments
    release_notes TEXT                                   -- Release notes for this version
);

-- ============================================================================
-- INDEX RECOMMENDATIONS (Optional - Add if needed for performance)
-- ============================================================================

-- Index on created_at for chronological queries
-- CREATE INDEX IF NOT EXISTS idx_dataset_versions_created ON dataset_versions(created_at);

-- Index on is_production for finding current production version
-- CREATE INDEX IF NOT EXISTS idx_dataset_versions_production ON dataset_versions(is_production);

-- ============================================================================
-- FIELD EXPLANATIONS
-- ============================================================================

-- dataset_version:
--   Unique identifier for this dataset version.
--   Recommended format: Semantic versioning (v1.0.0, v1.1.0, v2.0.0)
--   Can also use timestamps: "dataset_20250101_120000"
--   Examples: "v1.0.0", "v2.0.0", "dataset_2025Q1"

-- created_at:
--   When this dataset version was created.
--   Automatically set to current timestamp.
--   ISO 8601 format: "2025-01-01T12:34:56Z"

-- description:
--   Human-readable description of this dataset version.
--   Examples:
--     - "Initial production dataset with 10K samples"
--     - "Added Mumbai data, filtered low-quality images"
--     - "Balanced dataset with equal city representation"

-- total_samples:
--   Total number of learning samples included in this version.
--   Count from learning_samples table at time of version creation.
--   Example: 10000

-- total_labels:
--   Total number of HITL labels included in this version.
--   Count from hitl_labels table at time of version creation.
--   May be greater than total_samples if multiple labels per sample.
--   Example: 12000 (10K samples, some have multiple labels)

-- samples_with_corrections:
--   Number of samples that have at least one 'changed' label.
--   Indicates how many samples had detector errors.
--   Example: 1500 (15% correction rate)

-- samples_confirmed_correct:
--   Number of samples that have at least one 'correct' label.
--   Indicates detector accuracy on labeled samples.
--   Example: 8000 (80% confirmed correct)

-- samples_unsure:
--   Number of samples that have 'unsure' labels.
--   Indicates ambiguous or poor-quality samples.
--   May be excluded from training.
--   Example: 500 (5% unsure)

-- source_cities:
--   Which cities contributed data to this version.
--   Can be JSON array: '["city_mumbai", "city_delhi", "city_bangalore"]'
--   Or CSV: "city_mumbai,city_delhi,city_bangalore"
--   Useful for understanding data diversity and bias.

-- date_range_start:
--   Earliest detection timestamp of samples in this version.
--   Helps understand temporal coverage.
--   ISO 8601 format: "2024-01-01T00:00:00Z"

-- date_range_end:
--   Latest detection timestamp of samples in this version.
--   Helps understand temporal coverage.
--   ISO 8601 format: "2025-01-01T00:00:00Z"

-- is_production:
--   Boolean flag indicating if this is the current production dataset.
--   Only one version should have is_production = TRUE at a time.
--   Used to identify which dataset to use for production training.

-- is_archived:
--   Boolean flag indicating if this version has been archived.
--   Archived versions are kept for historical reference but not used.
--   Can be used to hide old versions from active use.

-- average_confidence:
--   Average detection confidence across all samples in this version.
--   Can indicate overall data quality.
--   Example: 0.87 (87% average confidence)

-- label_agreement_rate:
--   Percentage of samples where all labels agree (if multiple labels exist).
--   High agreement = consistent labeling, low ambiguity.
--   Example: 0.95 (95% agreement rate)

-- used_in_training_runs:
--   Counter tracking how many training runs have used this version.
--   Incremented each time this version is used for training.
--   Example: 5 (used in 5 different training runs)

-- last_used_at:
--   Timestamp of the most recent training run using this version.
--   Helps identify unused or stale versions.
--   ISO 8601 format: "2025-01-01T12:34:56Z"

-- metadata:
--   Additional version-specific metadata in JSON or text format.
--   Can store arbitrary information like:
--     - Preprocessing parameters
--     - Filtering criteria
--     - Data augmentation settings
--   Example JSON: '{"image_size": [640, 480], "format": "jpeg", "augmentation": true}'

-- release_notes:
--   Detailed release notes explaining what changed in this version.
--   Similar to software release notes.
--   Examples:
--     - "v1.0.0: Initial release with 10K samples from Mumbai"
--     - "v1.1.0: Added 5K samples from Delhi, fixed labeling issues"
--     - "v2.0.0: Major update with 50K samples, rebalanced by city"

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Get latest dataset version:
-- SELECT * FROM dataset_versions
-- ORDER BY created_at DESC
-- LIMIT 1;

-- Get current production dataset:
-- SELECT * FROM dataset_versions
-- WHERE is_production = TRUE;

-- List all versions with statistics:
-- SELECT dataset_version,
--        created_at,
--        total_samples,
--        total_labels,
--        ROUND(100.0 * samples_with_corrections / total_samples, 2) as correction_rate_pct,
--        used_in_training_runs
-- FROM dataset_versions
-- ORDER BY created_at DESC;

-- Find versions from a specific time period:
-- SELECT * FROM dataset_versions
-- WHERE date_range_start >= '2024-01-01'
--   AND date_range_end <= '2024-12-31';

-- Compare two versions:
-- SELECT
--     v1.dataset_version as version_1,
--     v1.total_samples as v1_samples,
--     v2.dataset_version as version_2,
--     v2.total_samples as v2_samples,
--     (v2.total_samples - v1.total_samples) as sample_delta
-- FROM dataset_versions v1
-- CROSS JOIN dataset_versions v2
-- WHERE v1.dataset_version = 'v1.0.0'
--   AND v2.dataset_version = 'v1.1.0';

-- ============================================================================
-- VERSIONING WORKFLOW
-- ============================================================================

-- Step 1: Accumulate Data
--   - City clients send samples and labels to learning store
--   - Data continuously accumulates in learning_samples and hitl_labels tables
--   - No versioning yet - just raw data collection

-- Step 2: Create Version Snapshot
--   - Periodically (e.g., monthly, quarterly), create a new dataset version
--   - Count samples and labels
--   - Calculate statistics (correction rate, agreement rate, etc.)
--   - Insert new row into dataset_versions table
--   - Tag samples with this version in learning_samples.training_dataset_version

-- Step 3: Use Version in Training
--   - Training pipeline specifies which version to use
--   - Query learning_samples and hitl_labels filtered by version
--   - Version ensures exact same data is used if training is repeated
--   - Increment used_in_training_runs counter

-- Step 4: Promote to Production (Optional)
--   - After validating new model, mark version as production
--   - Set is_production = TRUE for new version
--   - Set is_production = FALSE for old production version

-- Step 5: Archive Old Versions (Optional)
--   - Old versions can be archived but kept for historical reference
--   - Set is_archived = TRUE
--   - May move associated samples to cold storage

-- ============================================================================
-- VERSIONING STRATEGIES
-- ============================================================================

-- Strategy 1: Semantic Versioning
--   Format: vMAJOR.MINOR.PATCH
--   - MAJOR: Breaking changes (new labeling schema, different classes)
--   - MINOR: New data added (more samples, more cities)
--   - PATCH: Bug fixes (corrected labels, filtered bad samples)
--   Examples: v1.0.0 -> v1.1.0 -> v2.0.0

-- Strategy 2: Date-based Versioning
--   Format: dataset_YYYYMMDD or YYYY_QN
--   Examples: "dataset_20250101", "2025_Q1", "2025_Jan"
--   Advantage: Immediately clear when data was collected

-- Strategy 3: Named Releases
--   Format: Descriptive names
--   Examples: "initial", "production_v1", "balanced_dataset"
--   Advantage: Memorable and descriptive

-- Recommendation: Use semantic versioning (v1.0.0) with descriptive names in description field

-- ============================================================================
-- REPRODUCING TRAINING RUNS
-- ============================================================================

-- To reproduce a training run:
-- 1. Identify which dataset_version was used
-- 2. Query learning_samples where training_dataset_version = that version
-- 3. Join with hitl_labels to get ground truth labels
-- 4. Apply same preprocessing and augmentation (stored in metadata)
-- 5. Should get same dataset as original training run

-- Example query to reproduce dataset for version v1.0.0:
-- SELECT
--     ls.sample_id,
--     ls.image_reference,
--     ls.plate_text as detected_plate,
--     ls.confidence,
--     hl.label_status,
--     hl.corrected_plate,
--     COALESCE(hl.corrected_plate, ls.plate_text) as ground_truth
-- FROM learning_samples ls
-- LEFT JOIN hitl_labels hl ON ls.sample_id = hl.sample_id
-- WHERE ls.training_dataset_version LIKE '%v1.0.0%'
--   AND (hl.label_status != 'unsure' OR hl.label_status IS NULL);

-- ============================================================================
-- NOTES FOR IMPLEMENTATION
-- ============================================================================

-- 1. Version Creation:
--    - Automate version creation with scheduled jobs or manual trigger
--    - Calculate all statistics when creating version
--    - Use transactions to ensure consistency
--    - Tag samples with version in learning_samples.training_dataset_version

-- 2. Immutability:
--    - Once created, versions should NOT be modified
--    - New data = new version
--    - Ensures reproducibility and prevents confusion

-- 3. Storage:
--    - Old versions can be moved to cold storage
--    - Keep metadata in this table for reference
--    - Images can be archived but metadata remains accessible

-- 4. Production Management:
--    - Clearly mark which version is production
--    - Have rollback plan (can switch back to previous version)
--    - Test new versions before promoting to production

-- 5. Comparison and Analysis:
--    - Regularly compare versions to understand data growth
--    - Track correction rates over time (improving detector?)
--    - Monitor data diversity (balanced across cities?)

-- 6. Integration with Training:
--    - Training pipeline should always specify version
--    - Log which version was used in training run metadata
--    - Enable easy comparison across model versions

-- ============================================================================
