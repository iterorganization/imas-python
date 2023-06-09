# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

from contextlib import contextmanager
from typing import Any, Callable, Iterator, Tuple, Union
from types import ModuleType

from imaspy.ids_defs import (
    CLOSEST_INTERP,
    LINEAR_INTERP,
    PREVIOUS_INTERP,
    UNDEFINED_INTERP,
)

INTERP_MODES = (
    CLOSEST_INTERP,
    LINEAR_INTERP,
    PREVIOUS_INTERP,
    UNDEFINED_INTERP,
)


class UalContext:
    """Helper class that wraps UAL contexts.

    Provides:

    - Object oriented wrappers around AL lowlevel methods which require a context
    - Context managers for creating and automatically ending UAL actions
    """

    def __init__(self, ctx: int, ull: ModuleType) -> None:
        """Construct a new UalContext object

        Args:
            ctx: Context identifier returned by the AL
            ull: ``imas._ual_lowlevel`` python module that returned this context
        """
        self.ctx = ctx
        self.ull = ull

    @contextmanager
    def global_action(self, path: str, rwmode: int) -> Iterator["UalContext"]:
        """Begin a new ual global action for use in a ``with`` context.

        Args:
            path: access layer path for this global action: ``<idsname>[/<occurrence>]``
            rwmode: read-only or read-write operation mode: ``READ_OP``/``WRITE_OP``

        Yields:
            ctx: The created context.
        """
        ctx = self._begin_action(self.ull.ual_begin_global_action, path, rwmode)
        try:
            yield ctx
        finally:
            self.ull.ual_end_action(ctx.ctx)

    @contextmanager
    def slice_action(
        self, path: str, rwmode: int, time_requested: float, interpolation_method: int
    ) -> Iterator["UalContext"]:
        """Begin a new ual slice action for use in a ``with`` context.

        Args:
            path: access layer path for this global action: ``<idsname>[/<occurrence>]``
            rwmode: read-only or read-write operation mode: ``READ_OP``/``WRITE_OP``
            time_requested: time-point requested. Use ``UNDEFINED_TIME`` for put_slice.
            interpolation-method: interpolation method to use: ``CLOSEST_INTERP``,
                ``LINEAR_INTERP`` or ``PREVIOUS_INTERP`` for get_slice;
                ``UNDEFINED_INTERP`` for put_slice.

        Yields:
            ctx: The created context.
        """
        if interpolation_method not in INTERP_MODES:
            raise ValueError(
                "get_slice called with unexpected interpolation method: "
                f"{interpolation_method}"
            )
        ctx = self._begin_action(
            self.ull.ual_begin_slice_action,
            path,
            rwmode,
            time_requested,
            interpolation_method,
        )
        try:
            yield ctx
        finally:
            self.ull.ual_end_action(ctx.ctx)

    @contextmanager
    def arraystruct_action(
        self, path: str, timebase: str, size: int
    ) -> Iterator[Tuple["UalContext", int]]:
        """Begin a new ual arraystruct action for use in a ``with`` context.

        Args:
            path: relative access layer path within this context
            timebase: path to the timebase for this coordinate (an empty string for
                non-dynamic array of structures)
            size: the size of the array of structures (only relevant when writing data)

        Yields:
            ctx: The created context.
            size: The size of the array of structures (only relevant when reading data)
        """
        ctx, size = self._begin_action(
            self.ull.ual_begin_arraystruct_action, path, timebase, size
        )
        try:
            yield ctx, size
        finally:
            self.ull.ual_end_action(ctx.ctx)

    def _begin_action(
        self, action: Callable, *args: Any
    ) -> Union["UalContext", Tuple["UalContext", Any]]:
        """Helper method for creating new contexts."""
        status, ctx, *rest = action(self.ctx, *args)
        if status != 0:
            raise RuntimeError(f"Error calling {action.__name__}: {status=}")
        if rest:
            return UalContext(ctx, self.ull), *rest
        return UalContext(ctx, self.ull)

    def iterate_over_arraystruct(self, step: int) -> None:
        """Call ual_iterate_over_arraystruct with this context."""
        status = self.ull.ual_iterate_over_arraystruct(self.ctx, step)
        if status != 0:
            raise RuntimeError(f"Error iterating over arraystruct: {status=}")

    def read_data(self, path: str, timebasepath: str, datatype: int, dim: int) -> Any:
        """Call ual_read_data with this context."""
        status, data = self.ull.ual_read_data(
            self.ctx, path, timebasepath, datatype, dim
        )
        if status != 0:
            raise RuntimeError(f"Error reading data at {path!r}: {status=}")
        return data

    def delete_data(self, path: str) -> None:
        """Call ual_delete_data with this context."""
        status = self.ull.ual_delete_data(self.ctx, path)
        if status != 0:
            raise RuntimeError(f"Error deleting data at {path!r}: {status=}")

    def write_data(self, path: str, timebasepath: str, data: Any) -> None:
        """Call ual_write_data with this context."""
        status = self.ull.ual_write_data(self.ctx, path, timebasepath, data)
        if status != 0:
            raise RuntimeError(f"Error writing data at {path!r}: {status=}")
