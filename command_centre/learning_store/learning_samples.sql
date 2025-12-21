-- ============================================================================
-- Command Centre Learning Store: Learning Samples Table
-- ============================================================================
--
-- PURPOSE:
--   Store curated detection samples from city clients for centralized learning.
--
-- CRITICAL NOTES:
--   - This table stores CURATED samples only (not all detections)
--   - City operational data remains in city databases
--   - Samples are sent by clients when they want to contribute to learning
--   - Images are stored externally; this table stores references only
--
-- DATA FLOW:
--   1. City client detects a plate
--   2. Client decides to contribute sample to learning (based on criteria)
--   3. Client sends sample metadata + image reference to Command Centre
--   4. Command Centre stores in this table
--   5. Training pipeline reads from this table
--
-- ISOLATION:
--   - City databases: Operational data (all detections, events, alerts)
--   - Learning store: Training data (curated samples + labels)
--   - These are completely separate databases
--
-- ============================================================================

CREATE TABLE IF NOT EXISTS learning_samples (
    -- Primary key: Unique identifier for this learning sample
    sample_id TEXT PRIMARY KEY,

    -- Source identification
    city_id TEXT NOT NULL,                    -- Which city contributed this sample
    camera_id TEXT,                           -- Which camera detected this (nullable)

    -- Detection information
    plate_text TEXT,                          -- Detected plate text (may be incorrect)
    confidence REAL,                          -- Detection confidence (0.0 - 1.0)

    -- Image storage
    image_reference TEXT NOT NULL,            -- Reference/URL to stored image (external storage)

    -- Metadata
    detection_timestamp TEXT,                 -- When was this originally detected (ISO 8601)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),  -- When was this sample added to learning store

    -- Additional context (optional, can be null)
    context_notes TEXT,                       -- Any additional context about this sample

    -- Sample source/type
    sample_type TEXT DEFAULT 'automatic',     -- 'automatic' | 'manual' | 'synthetic'

    -- Quality indicators
    image_quality_score REAL,                 -- Optional quality score for filtering

    -- Training usage tracking
    used_in_training BOOLEAN DEFAULT FALSE,   -- Has this been used in training yet?
    training_dataset_version TEXT             -- Which dataset version(s) include this sample
);

-- ============================================================================
-- INDEX RECOMMENDATIONS (Optional - Add if needed for performance)
-- ============================================================================

-- Index on city_id for filtering by city
-- CREATE INDEX IF NOT EXISTS idx_learning_samples_city ON learning_samples(city_id);

-- Index on created_at for chronological queries
-- CREATE INDEX IF NOT EXISTS idx_learning_samples_created ON learning_samples(created_at);

-- Index on used_in_training for filtering unused samples
-- CREATE INDEX IF NOT EXISTS idx_learning_samples_used ON learning_samples(used_in_training);

-- ============================================================================
-- FIELD EXPLANATIONS
-- ============================================================================

-- sample_id:
--   Unique identifier for this learning sample.
--   Format: "sample_<city>_<timestamp>_<random>" or UUID
--   Example: "sample_cityA_20250101_abc123"

-- city_id:
--   Identifier of the city that contributed this sample.
--   Allows tracking data provenance and ensuring balanced training data.
--   Example: "city_mumbai", "city_delhi"

-- camera_id:
--   Identifier of the specific camera that made this detection.
--   Nullable because some samples may be synthetic or manually created.
--   Example: "cam_001", "cam_highway_exit_5"

-- plate_text:
--   The detected plate text from the detector.
--   May be incorrect - that's why we collect HITL labels separately.
--   Nullable because some samples might be used for detection training only.
--   Example: "MH12AB1234", "DL3CAB1234"

-- confidence:
--   Detection confidence from the detector (0.0 to 1.0).
--   Nullable because confidence might not be available for manual/synthetic samples.
--   Example: 0.95

-- image_reference:
--   Reference or URL to the actual image stored in external storage (S3, GCS, etc.).
--   This table does NOT store image bytes directly.
--   Example: "s3://learning-images/sample_cityA_20250101_abc123.jpg"

-- detection_timestamp:
--   When this detection originally occurred at the city client.
--   ISO 8601 format: "2025-01-01T12:34:56Z"
--   Different from created_at (when sample was added to learning store).

-- created_at:
--   When this sample was added to the Command Centre learning store.
--   Automatically set to current timestamp.
--   ISO 8601 format: "2025-01-01T12:34:56Z"

-- context_notes:
--   Optional free-text field for additional context.
--   Examples: "Low light conditions", "Partial occlusion", "High traffic"

-- sample_type:
--   How this sample was obtained:
--   - 'automatic': Client automatically sent based on criteria
--   - 'manual': Human operator manually selected for contribution
--   - 'synthetic': Generated or augmented sample

-- image_quality_score:
--   Optional quality score (0.0 to 1.0) for filtering low-quality samples.
--   Can be used to prioritize high-quality samples during training.

-- used_in_training:
--   Boolean flag indicating if this sample has been used in any training run.
--   Allows finding fresh samples that haven't been used yet.

-- training_dataset_version:
--   Reference to dataset version(s) that include this sample.
--   Links to dataset_versions table.
--   Example: "v1.0.0", "v1.1.0,v1.2.0"

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Find all unused samples from a specific city:
-- SELECT * FROM learning_samples
-- WHERE city_id = 'city_mumbai'
--   AND used_in_training = FALSE
-- ORDER BY created_at DESC;

-- Count samples by city:
-- SELECT city_id, COUNT(*) as sample_count
-- FROM learning_samples
-- GROUP BY city_id;

-- Find high-confidence samples without labels yet:
-- SELECT ls.* FROM learning_samples ls
-- LEFT JOIN hitl_labels hl ON ls.sample_id = hl.sample_id
-- WHERE ls.confidence >= 0.9
--   AND hl.label_id IS NULL;

-- ============================================================================
-- NOTES FOR IMPLEMENTATION
-- ============================================================================

-- 1. Image Storage:
--    Images should be stored in external object storage (S3, GCS, etc.)
--    Only store references/URLs in this table

-- 2. Privacy:
--    Ensure no PII or sensitive operational data is included
--    Only store data necessary for training

-- 3. Data Retention:
--    Consider retention policies for old samples
--    May want to archive or delete samples after certain period

-- 4. Data Quality:
--    Implement validation when inserting samples
--    Ensure image_reference points to valid, accessible storage

-- 5. Scalability:
--    For large datasets, consider partitioning by created_at or city_id
--    Add indexes based on actual query patterns

-- ============================================================================
