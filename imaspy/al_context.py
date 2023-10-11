# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional, Tuple, Union
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

if TYPE_CHECKING:
    from imaspy.db_entry import DBEntry
    from imaspy.ids_convert import NBCPathMap


class ALContext:
    """Helper class that wraps Access Layer contexts.

    Provides:

    - Object oriented wrappers around AL lowlevel methods which require a context
    - Context managers for creating and automatically ending AL actions
    """

    def __init__(self, ctx: int, ull: ModuleType) -> None:
        """Construct a new ALContext object

        Args:
            ctx: Context identifier returned by the AL
            ull: ``imas._ual_lowlevel`` python module that returned this context
        """
        self.ctx = ctx
        self.ull = ull

    @contextmanager
    def global_action(self, path: str, rwmode: int) -> Iterator["ALContext"]:
        """Begin a new global action for use in a ``with`` context.

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
    ) -> Iterator["ALContext"]:
        """Begin a new slice action for use in a ``with`` context.

        Args:
            path: access layer path for this global action: ``<idsname>[/<occurrence>]``
            rwmode: read-only or read-write operation mode: ``READ_OP``/``WRITE_OP``
            time_requested: time-point requested. Use ``UNDEFINED_TIME`` for put_slice.
            interpolation_method: interpolation method to use: ``CLOSEST_INTERP``,
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
            self.ull.ual_begin_arraystruct_action, path, timebase, size
        )
        try:
            yield ctx, size
        finally:
            self.ull.ual_end_action(ctx.ctx)

    def _begin_action(
        self, action: Callable, *args: Any
    ) -> Union["ALContext", Tuple["ALContext", Any]]:
        """Helper method for creating new contexts."""
        status, ctx, *rest = action(self.ctx, *args)
        if status != 0:
            raise RuntimeError(f"Error calling {action.__name__}: {status=}")
        if rest:
            return ALContext(ctx, self.ull), *rest
        return ALContext(ctx, self.ull)

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


class LazyALContext:
    """Replacement for ALContext that is used during lazy loading.

    This class implements ``global_action``, ``slice_action`` and ``read_data``, such
    that it can be used as a drop-in replacement in ``imaspy.db_entry._get_children``
    and only custom logic is needed for IDSStructArray there.

    This class tracks:

    - The DBEntry object which was used for get() / get_slice().
    - The context object from that DBEntry (such that we can detect if the underlying AL
      context was closed or replaced).
    - Potentially a parent LazyALContext for nested contexts (looking at you,
      arraystruct_action!).
    - The ALContext method and arguments that we need to call on the ALContext we obtain
      from our parent, to obtain the actual ALContext we should use for loading data.
    - The NBC map that ``imaspy.db_entry._get_children`` needs when lazy loading
      children of an IDSStructArray.

    When constructing a LazyALContext, you need to supply either the ``dbentry`` and
    ``nbc_map``, or a ``parent_ctx``.
    """

    def __init__(
        self,
        parent_ctx: Optional["LazyALContext"] = None,
        method: Optional[Callable] = None,
        args: Tuple = (),
        *,
        dbentry: Optional["DBEntry"] = None,
        nbc_map: Optional["NBCPathMap"] = None,
    ) -> None:
        self.dbentry = dbentry or (parent_ctx and parent_ctx.dbentry)
        """DBEntry object that created us, or our parent."""
        self.dbentry_ctx = self.dbentry._db_ctx
        """The ALContext of the DBEntry at the time of get/get_slice."""
        self.parent_ctx = parent_ctx
        """Optional parent context that provides our parent ALContext."""
        self.method = method
        """Method we need to call with our parent ALContext to get our ALContext."""
        self.args = args
        """Additional arguments we need to supply to self.method"""
        self.nbc_map = nbc_map or (parent_ctx and parent_ctx.nbc_map)
        """NBC map for _get_children() when lazy loading IDSStructArray items."""

    @contextmanager
    def get_context(self) -> Iterator[ALContext]:
        """Create and yield the actual ALContext."""
        if self.dbentry._db_ctx is not self.dbentry_ctx:
            raise RuntimeError(
                "Cannot lazy load the requested data: the data entry is no longer "
                "available for reading. Hint: did you close() the DBEntry?"
            )

        if self.parent_ctx:
            # First convert our parent LazyALContext to an actual ALContext
            with self.parent_ctx.get_context() as parent:
                # Now we can create our ALContext:
                with self.method(parent, *self.args) as ctx:
                    yield ctx

        else:
            yield self.dbentry_ctx

    @contextmanager
    def global_action(self, path: str, rwmode: int) -> Iterator["LazyALContext"]:
        """Lazily start a lowlevel global action, see :meth:`ALContext.global_action`"""
        yield LazyALContext(self, ALContext.global_action, (path, rwmode))

    @contextmanager
    def slice_action(
        self, path: str, rwmode: int, time_requested: float, interpolation_method: int
    ) -> Iterator["LazyALContext"]:
        """Lazily start a lowlevel slice action, see :meth:`ALContext.slice_action`"""
        yield LazyALContext(
            self,
            ALContext.slice_action,
            (path, rwmode, time_requested, interpolation_method),
        )

    @contextmanager
    def lazy_arraystruct_action(
        self, path: str, timebase: str, item: Optional[int]
    ) -> Iterator[Tuple[Optional["LazyALContext"], int]]:
        """Perform an arraystruct action on this lazy AL context.

        Constructs the actual ALContext to obtain the size of the stored AoS, and yields
        a new LazyALContext for the given item.

        Args:
            path: relative access layer path within this context
            timebase: path to the timebase for this coordinate (an empty string for
                non-dynamic array of structures)
            item: index of the item to construct the new lazy context for. May be None
                to just get the size of the AoS.

        Yields:
            lazy_ctx: LazyALContext that can be used by the item within this AoS
            size: number of items stored in this AoS
        """
        with self.get_context() as ctx:
            with ctx.arraystruct_action(path, timebase, 0) as (new_ctx, size):
                args = (path, timebase, item)
                lazy_ctx = None
                if item is not None:
                    lazy_ctx = LazyALContext(self, self._get_aos_context, args)
                yield (lazy_ctx, size)

    @contextmanager
    def _get_aos_context(
        self, ctx: ALContext, path: str, timebase: str, item: Optional[int]
    ) -> Iterator["LazyALContext"]:
        """Helper method that iterates to the provided item and yields the ALContext."""
        with ctx.arraystruct_action(path, timebase, 0) as (new_ctx, size):
            assert 0 <= item < size
            new_ctx.iterate_over_arraystruct(item)
            yield new_ctx

    def read_data(self, path: str, timebasepath: str, datatype: int, dim: int) -> Any:
        """Lazily read data from the backend, see :meth:`AlContext.read_data`."""
        return LazyData(self, path, timebasepath, datatype, dim)


class LazyData:
    """Lazy loaded data reference.

    Can be assigned to an IDSPrimitive, allowing it to read the actual data from the
    lowlevel backend when it is requested.

    Args:
        ctx: provides the context to load the data.
        path: see :meth:`ALContext.read_data`
        timebasepath: see :meth:`ALContext.read_data`
        datatype: see :meth:`ALContext.read_data`
        dim: see :meth:`ALContext.read_data`
    """

    def __init__(
        self, ctx: LazyALContext, path: str, timebasepath: str, datatype: int, dim: int
    ) -> None:
        self.ctx = ctx
        self.path = path
        self.timebasepath = timebasepath
        self.datatype = datatype
        self.dim = dim

    def get(self) -> Any:
        """Read and return the data from the lowlevel"""
        with self.ctx.get_context() as ctx:
            return ctx.read_data(self.path, self.timebasepath, self.datatype, self.dim)
