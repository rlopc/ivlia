class StartupError(Exception):
    """ivlia must not start. The message says what fails and is shown as is."""


class ConfigError(StartupError):
    """The configuration is invalid."""
