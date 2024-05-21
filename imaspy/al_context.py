# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""Object-oriented interface to the IMAS lowlevel.
"""

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Iterator, List, Optional, Tuple

from imaspy.exception import LowlevelError
from imaspy.ids_defs import (
    CLOSEST_INTERP,
    LINEAR_INTERP,
    PREVIOUS_INTERP,
    UNDEFINED_INTERP,
)
from imaspy.imas_interface import ll_interface

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

    def __init__(self, ctx: int) -> None:
        """Construct a new ALContext object

        Args:
            ctx: Context identifier returned by the AL
        """
        self.ctx = ctx

    def __enter__(self) -> "ALContext":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        ll_interface.end_action(self.ctx)

    def global_action(self, path: str, rwmode: int) -> "ALContext":
        """Begin a new global action for use in a ``with`` context.

        Args:
            path: access layer path for this global action: ``<idsname>[/<occurrence>]``
            rwmode: read-only or read-write operation mode: ``READ_OP``/``WRITE_OP``

        Returns:
            The created context.
        """
        status, ctx = ll_interface.begin_global_action(self.ctx, path, rwmode)
        if status != 0:
            raise LowlevelError("global_action", status)
        return ALContext(ctx)

    def slice_action(
        self, path: str, rwmode: int, time_requested: float, interpolation_method: int
    ) -> "ALContext":
        """Begin a new slice action for use in a ``with`` context.

        Args:
            path: access layer path for this global action: ``<idsname>[/<occurrence>]``
            rwmode: read-only or read-write operation mode: ``READ_OP``/``WRITE_OP``
            time_requested: time-point requested. Use ``UNDEFINED_TIME`` for put_slice.
            interpolation_method: interpolation method to use: ``CLOSEST_INTERP``,
                ``LINEAR_INTERP`` or ``PREVIOUS_INTERP`` for get_slice;
                ``UNDEFINED_INTERP`` for put_slice.

        Returns:
            The created context.
        """
        if interpolation_method not in INTERP_MODES:
            raise ValueError(
                "get_slice called with unexpected interpolation method: "
                f"{interpolation_method}"
            )
        status, ctx = ll_interface.begin_slice_action(
            self.ctx,
            path,
            rwmode,
            time_requested,
            interpolation_method,
        )
        if status != 0:
            raise LowlevelError("slice_action", status)
        return ALContext(ctx)

    def arraystruct_action(
        self, path: str, timebase: str, size: int
    ) -> "ALArrayStructContext":
        """Begin a new arraystruct action for use in a ``with`` context.

        Args:
            path: relative access layer path within this context
            timebase: path to the timebase for this coordinate (an empty string for
                non-dynamic array of structures)
            size: the size of the array of structures (only relevant when writing data)

        Returns:
            The created context.
        """
        status, ctx, size = ll_interface.begin_arraystruct_action(
            self.ctx, path, timebase, size
        )
        if status != 0:
            raise LowlevelError("arraystruct_action", status)
        return ALArrayStructContext(ctx, size)

    def read_data(self, path: str, timebasepath: str, datatype: int, dim: int) -> Any:
        """Call ual_read_data with this context."""
        status, data = ll_interface.read_data(
            self.ctx, path, timebasepath, datatype, dim
        )
        if status != 0:
            raise LowlevelError(f"read data at {path!r}", status)
        return data

    def delete_data(self, path: str) -> None:
        """Call ual_delete_data with this context."""
        status = ll_interface.delete_data(self.ctx, path)
        if status != 0:
            raise LowlevelError(f"delete data at {path!r}", status)

    def write_data(self, path: str, timebasepath: str, data: Any) -> None:
        """Call ual_write_data with this context."""
        status = ll_interface.write_data(self.ctx, path, timebasepath, data)
        if status != 0:
            raise LowlevelError(f"write data at {path!r}: {status=}")

    def list_all_occurrences(self, ids_name: str) -> List[int]:
        """List all occurrences of this IDS."""
        status, occurrences = ll_interface.get_occurrences(self.ctx, ids_name)
        if status != 0:
            raise LowlevelError(f"list occurrences for {ids_name!r}", status)
        if occurrences is not None:
            return list(occurrences)
        return []


class ALArrayStructContext(ALContext):
    """Helper class that wraps contexts created through al_begin_arraystruct_action."""

    def __init__(self, ctx, size):
        """Construct a new ALContext object

        Args:
            ctx: Context identifier returned by the AL
            size: size of the AoS returned by the AL
        """
        self.ctx = ctx
        self.size = size

    def __enter__(self):
        return self, self.size

    def iterate_over_arraystruct(self, step: int) -> None:
        """Call ual_iterate_over_arraystruct with this context."""
        status = ll_interface.iterate_over_arraystruct(self.ctx, step)
        if status != 0:
            raise LowlevelError("iterate over arraystruct", status)


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
        time_mode: Optional[int] = None,
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
        if time_mode is None and parent_ctx:
            time_mode = parent_ctx.time_mode
        self.time_mode = time_mode
        """Time mode used by the IDS being lazy loaded."""

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
            LazyALContext that can be used by the item within this AoS and the number of
            items stored in this AoS.
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
