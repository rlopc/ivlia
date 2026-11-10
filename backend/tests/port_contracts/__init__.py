"""Contract tests that every adapter of a port must pass.

Each port has a base class here. An adapter's test subclasses it and provides
the `adapter` fixture. Base class names do not start with `Test`, so pytest
collects them only through their subclasses.
"""
