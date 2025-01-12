from dataclasses import dataclass
from typing import Callable


@dataclass
class IntrinsicArgs():
    arg_refs: list[str]
    result_register: str
    emit: Callable[[str], None]


Intrinsic = Callable[[IntrinsicArgs], None]

all_intrinsics: dict[str, Intrinsic] = {}


def _intrinsic(name: str) -> Callable[[Intrinsic], Intrinsic]:
    """Function decorator that registers that function as an intrinsic."""
    def wrapper(f: Intrinsic) -> Intrinsic:
        assert name not in all_intrinsics
        all_intrinsics[name] = f
        return f
    return wrapper


@_intrinsic("unary_-")
def unary_minus(a: IntrinsicArgs) -> None:
    a.emit(f'movq {a.arg_refs[0]}, {a.result_register}')
    a.emit(f'negq {a.result_register}')


@_intrinsic("unary_not")
def unary_not(a: IntrinsicArgs) -> None:
    a.emit(f'movq {a.arg_refs[0]}, {a.result_register}')
    a.emit(f'xorq $1, {a.result_register}')


@_intrinsic("+")
def plus(a: IntrinsicArgs) -> None:
    if a.result_register != a.arg_refs[0]:
        a.emit(f'movq {a.arg_refs[0]}, {a.result_register}')
    a.emit(f'addq {a.arg_refs[1]}, {a.result_register}')


@_intrinsic("-")
def minus(a: IntrinsicArgs) -> None:
    if a.result_register != a.arg_refs[0]:
        a.emit(f'movq {a.arg_refs[0]}, {a.result_register}')
    a.emit(f'subq {a.arg_refs[1]}, {a.result_register}')


@_intrinsic("*")
def multiply(a: IntrinsicArgs) -> None:
    if a.result_register != a.arg_refs[0]:
        a.emit(f'movq {a.arg_refs[0]}, {a.result_register}')
    a.emit(f'imulq {a.arg_refs[1]}, {a.result_register}')


@_intrinsic("/")
def divide(a: IntrinsicArgs) -> None:
    a.emit(f'movq {a.arg_refs[0]}, %rax')
    a.emit('cqto')  # TODO: explain
    a.emit(f'idivq {a.arg_refs[1]}')
    if a.result_register != '%rax':
        a.emit(f'movq %rax, {a.result_register}')


@_intrinsic("%")
def remainder(a: IntrinsicArgs) -> None:
    # Same as division, but remainder is in register 'rdx'
    a.emit(f'movq {a.arg_refs[0]}, %rax')
    a.emit('cqto')
    a.emit(f'idivq {a.arg_refs[1]}')
    if a.result_register != '%rdx':
        a.emit(f'movq %rdx, {a.result_register}')


@_intrinsic("==")
def eq(a: IntrinsicArgs) -> None:
    _int_comparison(a, 'sete')


@_intrinsic("!=")
def ne(a: IntrinsicArgs) -> None:
    _int_comparison(a, 'setne')


@_intrinsic("<")
def lt(a: IntrinsicArgs) -> None:
    _int_comparison(a, 'setl')


@_intrinsic("<=")
def le(a: IntrinsicArgs) -> None:
    _int_comparison(a, 'setle')


@_intrinsic(">")
def gt(a: IntrinsicArgs) -> None:
    _int_comparison(a, 'setg')


@_intrinsic(">=")
def ge(a: IntrinsicArgs) -> None:
    _int_comparison(a, 'setge')


def _int_comparison(a: IntrinsicArgs, setcc_insn: str) -> None:
    # We use 'al' and 'eax' below, which means the lower bytes of 'rax'
    a.emit('xor %rax, %rax')  # Clear all bits of rax
    a.emit(f'movq {a.arg_refs[0]}, %rdx')
    a.emit(f'cmpq {a.arg_refs[1]}, %rdx')
    # Set lowest byte of 'rax' to comparison result
    a.emit(f'{setcc_insn} %al')
    if a.result_register != '%rax':
        a.emit(f'movq %rax, {a.result_register}')
