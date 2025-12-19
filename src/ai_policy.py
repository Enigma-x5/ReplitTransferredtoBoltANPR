"""
AI Policy: Inference-Only Architecture Guard

CRITICAL: This file enforces the architectural constraint that client-side
deployments of this ANPR system are INFERENCE ONLY.

POLICY:
-------
- All AI model training, fine-tuning, and weight updates MUST occur in the
  centralized Command Centre, NOT in client deployments.
- Client builds consume pre-trained, validated models only.
- Any attempt to perform training operations in client code must fail loudly
  and immediately.

RATIONALE:
----------
This is an intentional architectural decision to ensure:
1. Model quality control and validation happen centrally
2. Computational resources are appropriately allocated
3. Client deployments remain lightweight and consistent
4. Training data governance and privacy are properly managed
5. Model versioning and rollback are controlled centrally

WARNING:
--------
DO NOT remove or bypass this policy in client deployments.
DO NOT add training loops, gradient updates, or model weight modifications
to client-side code.

If training capabilities are needed, they belong in the Command Centre
infrastructure, not in deployed client instances.
"""

# Inference-only enforcement flag
TRAINING_ALLOWED = False

# Policy version for tracking
POLICY_VERSION = "1.0.0"

# Clear statement of policy
POLICY_STATEMENT = (
    "This build is INFERENCE ONLY. "
    "Training, fine-tuning, gradient updates, and model weight modifications "
    "are strictly forbidden in client deployments. "
    "All learning must happen in the Command Centre."
)


class TrainingNotAllowedError(RuntimeError):
    """
    Exception raised when training operations are attempted in an inference-only build.

    This error indicates a violation of the architectural policy that client
    deployments must not perform any model training or weight updates.
    """
    pass


def block_training() -> None:
    """
    Enforcement function that prevents any training operations.

    This function should be called at the entry point of any code path that
    would perform model training, fine-tuning, or weight updates.

    Raises:
        TrainingNotAllowedError: Always raised to prevent training execution.

    Example:
        >>> block_training()
        Traceback (most recent call last):
        ...
        TrainingNotAllowedError: Training is disabled in client builds...
    """
    raise TrainingNotAllowedError(
        f"Training is disabled in client builds. {POLICY_STATEMENT}"
    )


def assert_inference_only() -> None:
    """
    Assert that the system is operating in inference-only mode.

    This can be used as a runtime check during initialization to ensure
    the policy is active.

    Raises:
        AssertionError: If TRAINING_ALLOWED is not False.
    """
    assert TRAINING_ALLOWED is False, (
        "TRAINING_ALLOWED must be False in client deployments. "
        "This is an architectural guard that must not be bypassed."
    )


def get_policy_info() -> dict:
    """
    Returns information about the current AI policy configuration.

    Returns:
        dict: Policy configuration details including version and statement.
    """
    return {
        "training_allowed": TRAINING_ALLOWED,
        "policy_version": POLICY_VERSION,
        "policy_statement": POLICY_STATEMENT,
        "mode": "inference_only"
    }
