from __future__ import annotations

import types
import weakref
from dataclasses import dataclass
from functools import reduce
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from ...utils import EventGuard, InnerError, log, log_do

Guard = Callable[[types.FrameType], bool]

if TYPE_CHECKING:
    from .variables import VariableBase

    CheckGuardInputT = TypeVar("CheckGuardInputT", bound=VariableBase)

# NOTE(SigureMo): [How to write Stringify Guard?]
# 1. we should capture free variables manually, the string cannot capture free
#    variables automatically.
# 2. Be aware that the comparison logic before and after stringify may be different.
# 3. we should compute as much as possible at "compile time" and encode the
#    computation in the Guard string, rather than passing it to runtime to minimize
#    runtime overhead.


@dataclass
class StringifyExpression:
    """
    Used to store string based expressions for generating Guard.
    """

    expr: str
    free_vars: dict[str, Any]

    def __post_init__(self):
        self.check_expr(self.expr)

    def check_expr(self, expr: str):
        try:
            pass
            # ast.parse(expr) # TODO(xiongkun): too slow
        except SyntaxError as e:
            raise InnerError(f"Invalid expression: {expr}") from e

    def __and__(self, other: StringifyExpression) -> StringifyExpression:
        return StringifyExpression(
            " and ".join([self.expr, other.expr]),
            union_free_vars(self.free_vars, other.free_vars),
        )

    def __hash__(self):
        if self.free_vars:
            return hash((self.expr, id(self)))
        else:
            return hash(self.expr)


def union_free_vars(*free_vars: dict[str, Any]):
    return {k: v for d in free_vars for k, v in d.items()}


def make_guard(stringify_guards: list[StringifyExpression]) -> Guard:
    """
    Make a guard from a list of StringifyExpression.

    For more design ideas, refer to the `Stringify guard <https://github.com/PaddlePaddle/PaddleSOT/blob/develop/docs/design/stringify-guard.md>`_ for details.

    Args:
        stringify_guards: a list of StringifyExpression.
    """
    with EventGuard(f"make_guard: ({len(stringify_guards)})"):
        num_guards = len(stringify_guards)
        if not num_guards:
            guard = lambda frame: True
            guard.expr = "lambda frame: True"
            return guard

        union_guard_expr = reduce(lambda x, y: x & y, stringify_guards)
        guard_string = f"lambda frame: {union_guard_expr.expr}"
        guard = eval(
            guard_string,
            union_guard_expr.free_vars,
        )
        log(3, f"[Guard]: {guard_string}\n")
        guard.expr = guard_string
        assert callable(guard), "guard must be callable."

        return guard


def support_weak_ref(obj):
    if isinstance(obj, types.FunctionType):
        return True
    return False


def check_guard(
    fn: Callable[[CheckGuardInputT], list[StringifyExpression]]
) -> Callable[[CheckGuardInputT], list[StringifyExpression]]:
    def wrapper(self: CheckGuardInputT) -> list[StringifyExpression]:
        assert (
            self.tracker.is_traceable()
        ), "Cannot make guard from a non-tracable guard variable."

        def guard_log():
            frame_value_tracer = self.tracker.trace_value_from_frame()
            print(
                f"[Guard]: guard_fn for {self}, tracker={self.tracker.__class__.__name__}, value={frame_value_tracer.expr}"
            )

        log_do(4, guard_log)
        return fn(self)

    return wrapper


@check_guard
def object_equal_stringify_guard(self) -> list[StringifyExpression]:
    frame_value_tracer = self.tracker.trace_value_from_frame()

    obj_free_var_name = f"__{self.id}"
    weak_ref_obj = self.get_py_value()
    if support_weak_ref(weak_ref_obj):
        weak_ref_obj = weakref.ref(self.get_py_value())
        return [
            StringifyExpression(
                f"{obj_free_var_name}() is not None and {frame_value_tracer.expr} == {obj_free_var_name}()",
                union_free_vars(
                    frame_value_tracer.free_vars,
                    {obj_free_var_name: weak_ref_obj},
                ),
            )
        ]
    return [
        StringifyExpression(
            f"{frame_value_tracer.expr} == {obj_free_var_name}",
            union_free_vars(
                frame_value_tracer.free_vars,
                {obj_free_var_name: self.get_py_value()},
            ),
        )
    ]
