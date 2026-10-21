"""Coordinate the two Nav2 legs of one delivery request."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable


PICKUP = 'pickup'
DROPOFF = 'dropoff'


class NavigationStatus(Enum):
    """Keep the reason a Nav2 leg ended distinct from its task stage."""

    SUCCEEDED = 'succeeded'
    CANCELED = 'canceled'
    TIMED_OUT = 'timed_out'
    REJECTED = 'rejected'
    UNAVAILABLE = 'unavailable'
    FAILED = 'failed'
    INTERNAL = 'internal'


class DeliveryStatus(Enum):
    """Terminal state to apply to the outer delivery action."""

    SUCCEEDED = 'succeeded'
    CANCELED = 'canceled'
    FAILED = 'failed'


@dataclass(frozen=True)
class NavigationOutcome:
    """Result of one NavigateToPose goal."""

    status: NavigationStatus
    message: str = ''


@dataclass(frozen=True)
class DeliveryOutcome:
    """Final result of the ordered pickup and drop-off legs."""

    status: DeliveryStatus
    failed_stage: str = ''
    message: str = ''

    @property
    def success(self) -> bool:
        return self.status is DeliveryStatus.SUCCEEDED


async def run_delivery(
    pickup_pose: Any,
    dropoff_pose: Any,
    navigate: Callable[[str, Any], Awaitable[NavigationOutcome]],
    report_stage: Callable[[str], None],
    cancel_requested: Callable[[], bool] = lambda: False,
) -> DeliveryOutcome:
    """Run drop-off only after pickup succeeds and cancellation stays clear."""
    for stage, pose in ((PICKUP, pickup_pose), (DROPOFF, dropoff_pose)):
        if cancel_requested():
            return DeliveryOutcome(
                DeliveryStatus.CANCELED,
                message=f'Delivery canceled before {stage}.',
            )

        report_stage(stage)
        try:
            outcome = await navigate(stage, pose)
        except Exception as exc:
            return DeliveryOutcome(
                DeliveryStatus.FAILED, 'internal',
                f'{stage} internal navigation error: {exc}',
            )
        if outcome.status is NavigationStatus.INTERNAL:
            return DeliveryOutcome(
                DeliveryStatus.FAILED, 'internal',
                f'{stage} internal navigation error: {outcome.message}',
            )
        if outcome.status is NavigationStatus.TIMED_OUT:
            return DeliveryOutcome(
                DeliveryStatus.FAILED, stage, outcome.message,
            )
        if outcome.status is NavigationStatus.CANCELED:
            return DeliveryOutcome(
                DeliveryStatus.CANCELED, stage,
                f'{stage} canceled by user.',
            )
        if cancel_requested():
            return DeliveryOutcome(
                DeliveryStatus.CANCELED,
                message=f'Delivery canceled after {stage}.',
            )
        if outcome.status is not NavigationStatus.SUCCEEDED:
            return DeliveryOutcome(
                DeliveryStatus.FAILED, stage,
                outcome.message or f'{stage} navigation {outcome.status.value}',
            )

    return DeliveryOutcome(
        DeliveryStatus.SUCCEEDED, message='Pickup and drop-off reached.'
    )
