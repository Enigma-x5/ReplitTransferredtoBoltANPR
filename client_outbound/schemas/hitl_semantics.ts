/**
 * HITL Semantics - Human-In-The-Loop Label State Definitions
 *
 * SCHEMA ONLY - NO LOGIC ALLOWED
 *
 * This file defines the semantic meaning of human feedback states in the
 * license plate detection system.
 *
 * CRITICAL ARCHITECTURE:
 * ----------------------
 * HITL SEMANTICS ARE FOR CENTRAL INTELLIGENCE ONLY
 *
 * - Client collects human feedback and sends it to Command Centre
 * - Client does NOT learn from human feedback locally
 * - Client-side learning is STRICTLY FORBIDDEN
 * - All training happens in the Command Centre only
 * - This file is documentation/schema only
 *
 * These states are used when human operators review and label detection
 * events. The labels are sent to the Command Centre for future model
 * training but NEVER used for client-side model updates.
 *
 * DO NOT:
 * - Add validation logic
 * - Add runtime behavior
 * - Import this into client inference code
 * - Add client-side learning logic
 * - Implement model updates on the client
 * - Add TODOs suggesting client-side learning
 *
 * This is a pure schema/documentation file.
 */

/**
 * HITL Label State
 *
 * Represents the human operator's assessment of a detection result.
 *
 * REMINDER: These labels are sent to the Command Centre for FUTURE training.
 * The client does NOT use these labels to update its model locally.
 */
export type HITLLabelState = "correct" | "changed" | "unsure";

/**
 * HITL Label State Semantics
 *
 * Detailed explanation of each label state and its meaning for downstream
 * model training (which occurs in the Command Centre, NOT on the client).
 */
export const HITLSemantics = {
  /**
   * CORRECT STATE
   * =============
   *
   * Meaning:
   * - The detected plate text is verified as accurate by a human operator
   * - The detection system produced the correct result
   * - No changes were needed
   *
   * Usage in Training (Command Centre only):
   * - High-confidence positive example
   * - Validates the current model's performance
   * - Can be used to maintain model accuracy on similar cases
   *
   * Client Behavior:
   * - Client sends this label to Command Centre
   * - NO LEARNING occurs on the client
   * - Client model remains unchanged
   * - Client continues inference-only operation
   */
  correct: "correct" as const,

  /**
   * CHANGED STATE
   * =============
   *
   * Meaning:
   * - The detected plate text was incorrect
   * - A human operator manually corrected the detection
   * - The correction represents the ground truth
   *
   * Usage in Training (Command Centre only):
   * - Negative example with ground truth correction
   * - Indicates model weakness on this type of input
   * - Correction provides supervised learning signal
   * - Most valuable for model improvement
   *
   * Client Behavior:
   * - Client sends the correction to Command Centre
   * - Corrections are sent to Command Centre ONLY
   * - Client does NOT update any models locally
   * - Client does NOT learn from this correction
   * - Client continues using its existing model unchanged
   */
  changed: "changed" as const,

  /**
   * UNSURE STATE
   * ============
   *
   * Meaning:
   * - The image quality or plate visibility is too poor for reliable detection
   * - Even a human operator cannot confidently read the plate
   * - The data is not reliable as ground truth
   *
   * Usage in Training (Command Centre only):
   * - Should be EXCLUDED from training datasets
   * - Indicates low-quality input data
   * - May be used for data quality analysis
   * - Should not be used as supervised learning examples
   *
   * Client Behavior:
   * - Client sends this label to Command Centre for tracking
   * - Client does NOT learn from these labels
   * - Client model remains unchanged
   * - These labels are metadata only
   */
  unsure: "unsure" as const,
} as const;

/**
 * Type guard to check if a string is a valid HITL label state.
 *
 * NOTE: This is a TYPE GUARD ONLY, not validation logic.
 * This is for TypeScript type narrowing at compile time.
 * Do NOT use this for runtime validation in the inference pipeline.
 */
export function isHITLLabelState(value: string): value is HITLLabelState {
  return value === "correct" || value === "changed" || value === "unsure";
}

/**
 * REMINDER: This is a schema-only file.
 *
 * - No validation logic beyond type guards
 * - No runtime behavior
 * - No learning or training on client
 * - HITL labels are sent to Command Centre only
 * - Client does not learn from HITL feedback
 * - All intelligence happens in Command Centre
 * - Client remains inference-only
 * - This file is documentation/schema only
 *
 * CLIENT-SIDE LEARNING IS STRICTLY FORBIDDEN.
 */
