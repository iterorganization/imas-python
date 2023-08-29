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


class ALContext:
    """Helper class that wraps Access Layer contexts.

    Provides:

    - Object oriented wrappers around AL lowlevel methods which require a context
    - Context managers for creating and automatically ending AL actions
    """

    def __init__(self, ctx: int, ll: ModuleType) -> None:
        """Construct a new ALContext object

        Args:
            ctx: Context identifier returned by the AL
            ll: ``imas._al_lowlevel`` python module that returned this context
        """
        self.ctx = ctx
        self.ll = ll

    @contextmanager
    def global_action(self, path: str, rwmode: int) -> Iterator["ALContext"]:
        """Begin a new global action for use in a ``with`` context.

        Args:
            path: access layer path for this global action: ``<idsname>[/<occurrence>]``
            rwmode: read-only or read-write operation mode: ``READ_OP``/``WRITE_OP``

        Yields:
            ctx: The created context.
        """
        ctx = self._begin_action(self.ll.al_begin_global_action, path, rwmode)
        try:
            yield ctx
        finally:
            self.ll.al_end_action(ctx.ctx)

    @contextmanager
    def slice_action(
        self, path: str, rwmode: int, time_requested: float, interpolation_method: int
    ) -> Iterator["ALContext"]:
        """Begin a new slice action for use in a ``with`` context.

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
            self.ll.al_begin_slice_action,
            path,
            rwmode,
            time_requested,
            interpolation_method,
        )
        try:
            yield ctx
        finally:
            self.ll.al_end_action(ctx.ctx)

    @contextmanager
    def arraystruct_action(
        self, path: str, timebase: str, size: int
    ) -> Iterator[Tuple["ALContext", int]]:
        """Begin a new arraystruct action for use in a ``with`` context.

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
            self.ll.al_begin_arraystruct_action, path, timebase, size
        )
        try:
            yield ctx, size
        finally:
            self.ll.al_end_action(ctx.ctx)

    def _begin_action(
        self, action: Callable, *args: Any
    ) -> Union["ALContext", Tuple["ALContext", Any]]:
        """Helper method for creating new contexts."""
        status, ctx, *rest = action(self.ctx, *args)
        if status != 0:
            raise RuntimeError(f"Error calling {action.__name__}: {status=}")
        if rest:
            return ALContext(ctx, self.ll), *rest
        return ALContext(ctx, self.ll)

    def iterate_over_arraystruct(self, step: int) -> None:
        """Call al_iterate_over_arraystruct with this context."""
        status = self.ll.al_iterate_over_arraystruct(self.ctx, step)
        if status != 0:
            raise RuntimeError(f"Error iterating over arraystruct: {status=}")

    def read_data(self, path: str, timebasepath: str, datatype: int, dim: int) -> Any:
        """Call al_read_data with this context."""
        status, data = self.ll.al_read_data(
            self.ctx, path, timebasepath, datatype, dim
        )
        if status != 0:
            raise RuntimeError(f"Error reading data at {path!r}: {status=}")
        return data

    def delete_data(self, path: str) -> None:
        """Call al_delete_data with this context."""
        status = self.ll.al_delete_data(self.ctx, path)
        if status != 0:
            raise RuntimeError(f"Error deleting data at {path!r}: {status=}")

    def write_data(self, path: str, timebasepath: str, data: Any) -> None:
        """Call al_write_data with this context."""
        status = self.ll.al_write_data(self.ctx, path, timebasepath, data)
        if status != 0:
            raise RuntimeError(f"Error writing data at {path!r}: {status=}")
