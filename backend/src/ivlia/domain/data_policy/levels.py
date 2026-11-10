"""Data levels, from least to most sensitive."""

from enum import IntEnum


class DataLevel(IntEnum):
    """How far a piece of data may travel. Higher is more sensitive."""

    PUBLIC = 0
    """Any component, even an external one in the cloud."""
    INTERNAL = 1
    """Components on the local network."""
    PRIVATE = 2
    """Only the user's Mac. Unclassified data gets this level."""
    SECRET = 3
    """Never sent to models or logs."""
