# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.

import numpy as np


class ContextStore(dict):
    """Stores global UAL context

    A context is a sort of pointer but to where depends on the type of context:
      - PulseContext: identifies a specific entry in database
      - OperationContext: identifies a specific I/O operation (read/write,
        global/slice, which IDS, etc...) being performed on a specific
        PulseContext
      - ArraystructContext: identifies a array of structure node within the IDS
        for a specific operation

    The rest of the absolute path (from last context to leaf/data) is not stored
    in context but passed directly to ual_read and ual_write LL functions.
    Contexts have a fullPath() method that will return string with pseudo
    fullpath up to this context
    """

    def __setitem__(self, key, value):
        """Store context id (key) and full path (value)

        As context is stored globally within the LL-UAL beyond our reach,
        do not allow for duplicated contexts to be opened.
        """
        if key in self:
            raise RuntimeError(
                "Trying to set context {!s} to {!s}, but was not released. \
                Currently is {!s}".format(
                    key, value, self[key]
                )
            )
        else:
            super().__setitem__(key, value)

    def update(self, ctx, newCtx):
        if ctx not in self:
            raise KeyError("Trying to update non-existing context {!s}".format(ctx))
        super().__setitem__(ctx, newCtx)

    def decodeContextInfo(self, ctxLst=None):
        """Decode ual context info to Python-friendly format"""
        if ctxLst is None:
            ctxLst = self.keys()
        elif ctxLst is not None and not isinstance(ctxLst, list):
            ctxLst = list(ctxLst)
        if any(not np.issubdtype(type(ctx), np.integer) for ctx in ctxLst):
            raise ValueError("ctx identifier should be an integer")
        for ctx in ctxLst:
            # This seems to cause memory corruption
            # Sometimes..
            contextInfo = self._ull.ual_context_info(ctx)
            infoCopy = (contextInfo + ".")[:-1]
            info = {}
            for line in infoCopy.split("\n"):
                if line == "":
                    continue
                key, val = line.split("=")
                info[key.strip()] = val.strip()

    def strip_context(self, path: str, ctx: int) -> str:
        """Get the path relative to given context from an absolute path"""
        # TODO: This could be replaced with the fullPath() method provided by the LL-UAL
        if path.startswith(self[ctx]):
            # strip the context path as well as any numeric indices
            # (those are handled by the context store)
            return path[len(self[ctx]) :].lstrip("/0123456789")
        else:
            raise ValueError(
                "Could not strip context from absolute path {!s}, "
                "ctx: {!s}, store: {!s}".format(path, ctx, self)
            )


# Keep a single 'global' variable context_store
context_store = ContextStore()
