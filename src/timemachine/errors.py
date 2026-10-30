class TimeMachineError(Exception):
    """An actionable failure; no success guarantee was made."""


class ConflictError(TimeMachineError):
    """Current state does not safely match the planned operation."""


class IntegrityError(TimeMachineError):
    """Persisted or observed data violates an integrity invariant."""
