-- ============================================================================
-- Command Centre Learning Store: HITL Labels Table
-- ============================================================================
--
-- PURPOSE:
--   Store Human-In-The-Loop (HITL) labels and corrections for learning samples.
--
-- CRITICAL NOTES:
--   - This table stores HUMAN corrections to detector outputs
--   - Used for supervised learning and model improvement
--   - Labels come from operators reviewing detections at city clients
--   - Multiple labels may exist for the same sample (agreement/disagreement)
--
-- HITL SEMANTICS:
--   - "correct": Operator confirms the detection is correct
--   - "changed": Operator corrects the detection
--   - "unsure": Operator is uncertain (sample may be ambiguous)
--
-- DATA FLOW:
--   1. City client shows detection to operator
--   2. Operator reviews and provides feedback (correct/changed/unsure)
--   3. Client sends label to Command Centre
--   4. Command Centre stores in this table
--   5. Training pipeline uses labels as ground truth
--
-- ============================================================================

CREATE TABLE IF NOT EXISTS hitl_labels (
    -- Primary key: Unique identifier for this label
    label_id TEXT PRIMARY KEY,

    -- Foreign key: Links to the learning sample being labeled
    sample_id TEXT NOT NULL,
    -- FOREIGN KEY (sample_id) REFERENCES learning_samples(sample_id),
    -- Note: Uncomment above line when creating in actual database

    -- Label status: What did the operator say?
    label_status TEXT NOT NULL CHECK (label_status IN ('correct', 'changed', 'unsure')),

    -- Corrected value (only for 'changed' status)
    corrected_plate TEXT,                      -- The correct plate text (if changed)

    -- Label metadata
    labeled_at TEXT NOT NULL DEFAULT (datetime('now')),  -- When was this label created
    operator_id TEXT,                          -- Which operator provided this label (optional)
    city_id TEXT NOT NULL,                     -- Which city's operator labeled this

    -- Additional context
    correction_notes TEXT,                     -- Why was this changed? What was wrong?
    confidence_override REAL,                  -- Operator's confidence in their correction

    -- Label quality/source
    label_source TEXT DEFAULT 'review',        -- 'review' | 'correction' | 'validation'
    review_time_seconds INTEGER,               -- How long did operator spend reviewing?

    -- Disagreement tracking
    is_disputed BOOLEAN DEFAULT FALSE,         -- Has another operator disagreed with this label?
    dispute_resolution TEXT                    -- How was disagreement resolved? (if applicable)
);

-- ============================================================================
-- INDEX RECOMMENDATIONS (Optional - Add if needed for performance)
-- ============================================================================

-- Index on sample_id for finding all labels for a sample
-- CREATE INDEX IF NOT EXISTS idx_hitl_labels_sample ON hitl_labels(sample_id);

-- Index on label_status for filtering by status
-- CREATE INDEX IF NOT EXISTS idx_hitl_labels_status ON hitl_labels(label_status);

-- Index on city_id for per-city analytics
-- CREATE INDEX IF NOT EXISTS idx_hitl_labels_city ON hitl_labels(city_id);

-- Index on labeled_at for chronological queries
-- CREATE INDEX IF NOT EXISTS idx_hitl_labels_time ON hitl_labels(labeled_at);

-- ============================================================================
-- FIELD EXPLANATIONS
-- ============================================================================

-- label_id:
--   Unique identifier for this label.
--   Format: "label_<city>_<timestamp>_<random>" or UUID
--   Example: "label_cityA_20250101_xyz789"

-- sample_id:
--   Links this label to a specific learning sample.
--   Foreign key reference to learning_samples.sample_id
--   Example: "sample_cityA_20250101_abc123"

-- label_status:
--   The operator's verdict on this detection:
--
--   'correct' - The detector output is correct, no changes needed
--     Example: Detector said "MH12AB1234", operator confirms it's correct
--
--   'changed' - The detector output is incorrect, operator provides correction
--     Example: Detector said "MH12AB1Z34", operator corrects to "MH12AB1234"
--
--   'unsure' - Operator cannot determine correct answer (image unclear, etc.)
--     Example: Image is too blurry, plate partially occluded
--
--   Only these three values are allowed (CHECK constraint enforces this)

-- corrected_plate:
--   The CORRECT plate text according to the human operator.
--   Only populated when label_status = 'changed'
--   NULL for 'correct' (use original detection) or 'unsure' (no correction available)
--   Example: "MH12AB1234"

-- labeled_at:
--   Timestamp when this label was created.
--   Automatically set to current timestamp.
--   ISO 8601 format: "2025-01-01T12:34:56Z"

-- operator_id:
--   Identifier of the human operator who provided this label.
--   Optional - may be omitted for privacy reasons.
--   Useful for tracking inter-operator agreement and individual performance.
--   Example: "operator_001", "user_alice"

-- city_id:
--   Which city's operator provided this label.
--   Same as or related to the city_id in learning_samples.
--   Example: "city_mumbai", "city_delhi"

-- correction_notes:
--   Free-text explanation from operator about the correction.
--   Examples:
--     - "Character 'Z' should be '2' - OCR confusion"
--     - "Missing first digit due to dirt on plate"
--     - "Reflection caused misread of last character"

-- confidence_override:
--   Operator's confidence in their correction (0.0 to 1.0).
--   Useful for weighting labels during training.
--   Higher confidence = more certain = higher weight in training.
--   Example: 0.9 (very confident), 0.6 (somewhat confident)

-- label_source:
--   How was this label obtained?
--
--   'review' - Operator reviewed detection as part of normal workflow
--   'correction' - Operator explicitly correcting a known error
--   'validation' - Operator validating as part of quality control process
--
--   Helps understand label quality and context.

-- review_time_seconds:
--   How many seconds did the operator spend reviewing this sample?
--   Can indicate difficult/ambiguous samples (longer review time).
--   Can be used for operator performance analytics.
--   Example: 5 (quick review), 30 (careful examination)

-- is_disputed:
--   Boolean flag indicating if another operator provided a different label.
--   TRUE if there's disagreement between operators.
--   Disputed labels may need additional review or consensus process.

-- dispute_resolution:
--   How was the disagreement resolved?
--   Examples:
--     - "Senior operator review - confirmed correction"
--     - "Majority vote - 3/5 operators agreed"
--     - "Excluded from training - too ambiguous"
--   Only populated if is_disputed = TRUE

-- ============================================================================
-- LABEL SEMANTICS EXPLAINED
-- ============================================================================

-- Scenario 1: Detector got it right
--   Detector output: "MH12AB1234"
--   Operator: "This is correct"
--   Label: { label_status: 'correct', corrected_plate: NULL }
--   Training: Use original detection as ground truth

-- Scenario 2: Detector made a mistake
--   Detector output: "MH12AB1Z34" (confused '2' with 'Z')
--   Operator: "Should be MH12AB1234"
--   Label: { label_status: 'changed', corrected_plate: 'MH12AB1234' }
--   Training: Use corrected_plate as ground truth, mark detection as error

-- Scenario 3: Cannot determine correct answer
--   Detector output: "MH12XXXYYY"
--   Operator: "Image too blurry, can't read plate"
--   Label: { label_status: 'unsure', corrected_plate: NULL }
--   Training: Exclude this sample from training (ambiguous)

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Find all corrections (changed labels):
-- SELECT * FROM hitl_labels
-- WHERE label_status = 'changed'
-- ORDER BY labeled_at DESC;

-- Count labels by status:
-- SELECT label_status, COUNT(*) as count
-- FROM hitl_labels
-- GROUP BY label_status;

-- Find samples with multiple labels (potential disagreements):
-- SELECT sample_id, COUNT(*) as label_count
-- FROM hitl_labels
-- GROUP BY sample_id
-- HAVING COUNT(*) > 1;

-- Get all labels for a specific sample:
-- SELECT * FROM hitl_labels
-- WHERE sample_id = 'sample_cityA_20250101_abc123'
-- ORDER BY labeled_at;

-- Find samples that need dispute resolution:
-- SELECT * FROM hitl_labels
-- WHERE is_disputed = TRUE
--   AND dispute_resolution IS NULL;

-- Calculate correction rate by city:
-- SELECT city_id,
--        COUNT(*) as total_labels,
--        SUM(CASE WHEN label_status = 'changed' THEN 1 ELSE 0 END) as corrections,
--        ROUND(100.0 * SUM(CASE WHEN label_status = 'changed' THEN 1 ELSE 0 END) / COUNT(*), 2) as correction_rate_pct
-- FROM hitl_labels
-- GROUP BY city_id;

-- ============================================================================
-- MULTIPLE LABELS FOR SAME SAMPLE
-- ============================================================================

-- A single sample can have multiple labels from different operators.
-- This is INTENTIONAL and USEFUL:
--
-- 1. Inter-operator agreement: Do operators agree on the correction?
-- 2. Confidence estimation: Multiple "correct" labels increase confidence
-- 3. Dispute detection: Conflicting labels indicate ambiguous samples
-- 4. Majority voting: Can use consensus across multiple labels
--
-- Example: Sample "sample_001" has 3 labels:
--   - Operator A: status='correct'
--   - Operator B: status='correct'
--   - Operator C: status='changed', corrected='XYZ123'
--
-- Result: 2/3 agree on 'correct', 1/3 says 'changed'
-- Action: May need dispute resolution or senior review

-- ============================================================================
-- NOTES FOR IMPLEMENTATION
-- ============================================================================

-- 1. Ground Truth for Training:
--    When training models, use:
--    - Original detection if label_status = 'correct'
--    - corrected_plate if label_status = 'changed'
--    - Exclude sample if label_status = 'unsure'

-- 2. Multiple Labels Handling:
--    If sample has multiple labels:
--    - Check for consensus (all agree)
--    - Use majority vote if some disagree
--    - Flag for review if no clear consensus
--    - Consider operator confidence scores

-- 3. Label Quality:
--    - Track operator accuracy over time
--    - Weight labels by operator reliability
--    - Use review_time as quality indicator
--    - Flag labels that are disputed

-- 4. Privacy:
--    - operator_id should be anonymized or optional
--    - No PII should be in correction_notes
--    - Comply with data protection regulations

-- 5. Training Pipeline:
--    - Filter by label_status when building datasets
--    - Use confidence_override for sample weighting
--    - Exclude disputed labels unless resolved
--    - Balance dataset by label_status distribution

-- ============================================================================
