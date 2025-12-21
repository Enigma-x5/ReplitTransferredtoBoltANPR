/**
 * Label Schema - Human-in-the-Loop Label Data Contract
 *
 * SCHEMA ONLY - NO LOGIC ALLOWED
 *
 * This interface defines the structure of human corrections/labels sent FROM
 * the client TO the Command Centre for model training.
 *
 * CRITICAL ARCHITECTURE:
 * ----------------------
 * CLIENT ➜ COMMAND CENTRE (ONE-WAY OUTBOUND)
 *
 * - Client sends human labels/corrections to Command Centre
 * - Labels are aggregated by Command Centre for training
 * - Client does NOT learn from labels locally
 * - Client does NOT receive model updates through this interface
 * - No model updates occur on the client
 * - All training happens in the Command Centre
 *
 * This is a pure data contract with no validation, logic, or runtime behavior.
 *
 * DO NOT:
 * - Add validation logic
 * - Add runtime behavior
 * - Add local learning logic
 * - Add model distribution logic
 * - Implement training on the client
 */

/**
 * Label status values.
 */
export type LabelStatus = "correct" | "changed" | "unsure";

/**
 * Human-in-the-loop label payload sent from client to Command Centre.
 *
 * Represents a human correction or confirmation of a detection event.
 * These labels are sent to the Command Centre where they are aggregated
 * for future model training. The client never performs training locally.
 */
export interface HumanLabelSchema {
  /**
   * ID of the detection event being labeled.
   * References a previously sent DetectionEventSchema.
   */
  event_id: string;

  /**
   * The corrected license plate text as provided by the human operator.
   * Null if the human determined no plate was present.
   */
  corrected_plate: string | null;

  /**
   * Label status indicating the type of human action taken.
   *
   * - "correct": Human confirmed the detection was correct
   * - "changed": Human corrected the detection
   * - "unsure": Human was unsure and flagged for review
   */
  label_status: LabelStatus;

  /**
   * When the human provided this label (ISO 8601 format).
   * Example: "2024-01-15T14:35:00Z"
   */
  labeled_at: string;

  /**
   * Optional metadata about the labeling action.
   */
  metadata?: {
    /**
     * ID of the user who provided the label.
     */
    user_id?: string;

    /**
     * Time taken by the human to provide the label (in seconds).
     */
    labeling_duration_seconds?: number;

    /**
     * Optional notes from the human operator.
     */
    notes?: string;

    /**
     * Original detected text for reference.
     */
    original_plate_text?: string | null;

    /**
     * Original confidence score for reference.
     */
    original_confidence?: number;

    /**
     * Additional context about the labeling action.
     */
    [key: string]: any;
  };
}

/**
 * REMINDER: This is a schema-only file.
 *
 * - No validation logic
 * - No runtime behavior
 * - No learning or training on client
 * - Labels are sent to Command Centre only
 * - Client does not learn from labels
 * - No model updates occur on client
 * - All training happens in Command Centre
 */
