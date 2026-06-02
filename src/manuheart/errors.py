"""Typed exceptions for Manuheart."""


class ManuheartError(Exception):
    """Base exception for library boundary failures."""


class ConfigError(ManuheartError):
    """Configuration could not be loaded or normalized."""


class UnsupportedConfigFormatError(ConfigError):
    """The requested configuration format is unavailable or unknown."""
