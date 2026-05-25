from dataclasses import dataclass
from enum import IntEnum


@dataclass
class RequestStatus(IntEnum):
    OPEN = 0
    AI = 1
    OPERATOR = 2
    CLOSED = 3

operator_notification_threshold = [
    1, 5, 10, 15
]