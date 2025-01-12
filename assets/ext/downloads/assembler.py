import subprocess
import tempfile
from contextlib import nullcontext
from os import path
from typing import Any, Callable, ContextManager, TypeVar
import shutil
from pathlib import Path

T = TypeVar('T')


def assemble(
    assembly_code: str,
    output_file: str,
    workdir: str | None = None,
    tempfile_basename: str = 'program',
    link_with_c: bool = False,
    extra_libraries: list[str] = [],
) -> None:
    """Invokes 'as' and 'ld' to generate an executable file from Assembly code.

    The file is written to the given path.
    """
    _assemble(
        assembly_code=assembly_code,
        workdir=workdir,
        tempfile_basename=tempfile_basename,
        link_with_c=link_with_c,
        extra_libraries=extra_libraries,
        take_output=lambda f: shutil.move(f, output_file)
    )


def assemble_and_get_executable(
    assembly_code: str,
    workdir: str | None = None,
    tempfile_basename: str = 'program',
    link_with_c: bool = False,
    extra_libraries: list[str] = [],
) -> bytes:
    """Invokes 'as' and 'ld' to generate an executable file from Assembly code.

    The file is returned.
    """
    return _assemble(
        assembly_code=assembly_code,
        workdir=workdir,
        tempfile_basename=tempfile_basename,
        link_with_c=link_with_c,
        extra_libraries=extra_libraries,
        take_output=lambda f: Path(f).read_bytes()
    )


def _assemble(
    assembly_code: str,
    workdir: str | None,
    tempfile_basename: str,
    link_with_c: bool,
    extra_libraries: list[str],
    take_output: Callable[[str], T],
) -> T:
    if workdir is not None:
        wd = Path(workdir).absolute().as_posix()
        return _assemble_impl(assembly_code, wd, tempfile_basename, link_with_c, extra_libraries, take_output)
    else:
        with tempfile.TemporaryDirectory(prefix='compiler_') as wd:
            return _assemble_impl(assembly_code, wd, tempfile_basename, link_with_c, extra_libraries, take_output)


def _assemble_impl(
    assembly_code: str,
    workdir: str,
    tempfile_basename: str,
    link_with_c: bool,
    extra_libraries: list[str],
    take_output: Callable[[str], T],
) -> T:
    stdlib_asm = path.join(workdir, 'stdlib.s')
    stdlib_obj = path.join(workdir, 'stdlib.o')
    program_asm = path.join(workdir, f'{tempfile_basename}.s')
    program_obj = path.join(workdir, f'{tempfile_basename}.o')
    output_file = path.join(workdir, 'a.out')

    if link_with_c:
        final_stdlib_asm_code = drop_start_symbol(stdlib_asm_code)
    else:
        final_stdlib_asm_code = stdlib_asm_code

    with open(stdlib_asm, 'w') as f:
        f.write(final_stdlib_asm_code)
    with open(program_asm, 'w') as f:
        f.write(assembly_code)
    subprocess.run(['as', '-g', '-o' +
                    stdlib_obj, stdlib_asm], check=True)
    subprocess.run(['as', '-g', '-o' +
                    program_obj, program_asm], check=True)
    linker_flags = ['-static', *[f'-l{lib}' for lib in extra_libraries]]
    if link_with_c:
        # Linking with the C standard library correctly is complicated,
        # as evidenced by the complicated linker command shown by `cc -v something.c`.
        # Instead of trying to build the right `ld` command ourselves, we use the C compiler
        # to do the linking.
        subprocess.run(
            ['cc', '-o' + output_file, *linker_flags, stdlib_obj, program_obj], check=True)
    else:
        subprocess.run(
            ['ld', '-o' + output_file, *linker_flags, stdlib_obj, program_obj], check=True)
    return take_output(output_file)


def drop_start_symbol(code: str) -> str:
    return code.split('# BEGIN START')[0] + code.split('# END START')[1]


# WARNING: if you want to copy this into a separate file,
# replace all double backslashes `\\` with a single backslash `\`.
stdlib_asm_code: str = """
    .global _start
    .global print_int
    .global print_bool
    .global read_int
    .extern main
    .section .text

# BEGIN START (we skip this part when linking with C)
# ***** Function '_start' *****
# Calls function 'main' and halts the program

_start:
    call main
    movq $60, %rax
    xorq %rdi, %rdi
    syscall
# END START

# ***** Function 'print_int' *****
# Prints a 64-bit signed integer followed by a newline.
#
# We'll build up the digits to print on the stack.
# We generate the least significant digit first,
# and the stack grows downward, so that works out nicely.
#
# Algorithm:
#     push(newline)
#     if x < 0:
#         negative = true
#         x = -x
#     while x > 0:
#         push(digit for (x % 10))
#         x = x / 10
#     if negative:
#         push(minus sign)
#     syscall 'write' with pushed data
#     return the original argument
#
# Registers:
# - rdi = our input number, which we divide down as we go
# - rsp = stack pointer, pointing to the next character to emit.
# - rbp = pointer to one after the last byte of our output (which grows downward)
# - r9 = whether the number was negative
# - r10 = a copy of the original input, so we can return it
# - rax, rcx and rdx are used by intermediate computations

print_int:
    pushq %rbp               # Save previous stack frame pointer
    movq %rsp, %rbp          # Set stack frame pointer
    movq %rdi, %r10          # Back up original input
    decq %rsp                # Point rsp at first byte of output
                             # TODO: this non-alignment confuses debuggers. Use a different register?

    # Add newline as the last output byte
    movb $10, (%rsp)         # ASCII newline = 10
    decq %rsp

    # Check for zero and negative cases
    xorq %r9, %r9
    xorq %rax, %rax
    cmpq $0, %rdi
    je .Ljust_zero
    jge .Ldigit_loop
    incq %r9  # If < 0, set %r9 to 1

.Ldigit_loop:
    cmpq $0, %rdi
    je .Ldigits_done        # Loop done when input = 0

    # Divide rdi by 10
    movq %rdi, %rax
    movq $10, %rcx
    cqto
    idivq %rcx               # Sets rax = quotient and rdx = remainder

    movq %rax, %rdi          # The quotient becomes our remaining input
    cmpq $0, %rdx            # If the remainder is negative (because the input is), negate it
    jge .Lnot_negative
    negq %rdx
.Lnot_negative:
    addq $48, %rdx           # ASCII '0' = 48. Add the remainder to get the correct digit.
    movb %dl, (%rsp)         # Store the digit in the output
    decq %rsp
    jmp .Ldigit_loop

.Ljust_zero:
    movb $48, (%rsp)         # ASCII '0' = 48
    decq %rsp

.Ldigits_done:

    # Add minus sign if negative
    cmpq $0, %r9
    je .Lminus_done
    movb $45, (%rsp)         # ASCII '-' = 45
    decq %rsp
.Lminus_done:

    # Call syscall 'write'
    movq $1, %rax            # rax = syscall number for write
    movq $1, %rdi            # rdi = file handle for stdout
    # rsi = pointer to message
    movq %rsp, %rsi
    incq %rsi
    # rdx = number of bytes
    movq %rbp, %rdx
    subq %rsp, %rdx
    decq %rdx
    syscall

    # Restore stack registers and return the original input
    movq %rbp, %rsp
    popq %rbp
    movq %r10, %rax
    ret


# ***** Function 'print_bool' *****
# Prints either 'true' or 'false', followed by a newline.
print_bool:
    pushq %rbp               # Save previous stack frame pointer
    movq %rsp, %rbp          # Set stack frame pointer
    movq %rdi, %r10          # Back up original input

    cmpq $0, %rdi            # See if the argument is false (i.e. 0)
    jne .Ltrue
    movq $false_str, %rsi    # If so, set %rsi to the address of the string for false
    movq $false_str_len, %rdx       # and %rdx to the length of that string,
    jmp .Lwrite
.Ltrue:
    movq $true_str, %rsi     # otherwise do the same with the string for true.
    movq $true_str_len, %rdx

.Lwrite:
    # Call syscall 'write'
    movq $1, %rax            # rax = syscall number for write
    movq $1, %rdi            # rdi = file handle for stdout
    # rsi = pointer to message (already set above)
    # rdx = number of bytes (already set above)
    syscall
    
    # Restore stack registers and return the original input
    movq %rbp, %rsp
    popq %rbp
    movq %r10, %rax
    ret

true_str:
    .ascii "true\\n"
true_str_len = . - true_str
false_str:
    .ascii "false\\n"
false_str_len = . - false_str

# ***** Function 'read_int' *****
# Reads an integer from stdin, skipping non-digit characters, until a newline.
#
# To avoid the complexity of buffering, it very inefficiently
# makes a syscall to read each byte.
#
# It crashes the program if input could not be read.
read_int:
    pushq %rbp           # Save previous stack frame pointer
    movq %rsp, %rbp      # Set stack frame pointer
    pushq %r12           # Back up r12 since it's callee-saved
    pushq $0             # Reserve space for input
                         # (we only write the lowest byte,
                         # but loading 64-bits at once is easier)

    xorq %r9, %r9        # Clear r9 - it'll store the minus sign
    xorq %r10, %r10      # Clear r10 - it'll accumulate our output
                         # Skip r11 - syscalls destroy it
    xorq %r12, %r12      # Clear r12 - it'll count the number of input bytes read.

    # Loop until a newline or end of input is encountered
.Lloop:
    # Call syscall 'read'
    xorq %rax, %rax      # syscall number for read = 0
    xorq %rdi, %rdi      # file handle for stdin = 0
    movq %rsp, %rsi      # rsi = pointer to buffer
    movq $1, %rdx        # rdx = buffer size
    syscall              # result in rax = number of bytes read,
                         # or 0 on end of input, -1 on error

    # Check return value: either -1, 0 or 1.
    cmpq $0, %rax
    jg .Lno_error
    je .Lend_of_input
    jmp .Lerror

.Lend_of_input:
    cmpq $0, %r12
    je .Lerror           # If we've read no input, it's an error.
    jmp .Lend            # Otherwise complete reading this input.

.Lno_error:
    incq %r12            # Increment input byte counter
    movq (%rsp), %r8     # Load input byte to r8

    # If the input byte is 10 (newline), exit the loop
    cmpq $10, %r8
    je .Lend

    # If the input byte is 45 (minus sign), negate r9
    cmpq $45, %r8
    jne .Lnegation_done
    xorq $1, %r9
.Lnegation_done:

    # If the input byte is not between 48 ('0') and 57 ('9')
    # then skip it as a junk character.
    cmpq $48, %r8
    jl .Lloop
    cmpq $57, %r8
    jg .Lloop

    # Subtract 48 to get a digit 0..9
    subq $48, %r8

    # Shift the digit onto the result
    imulq $10, %r10
    addq %r8, %r10

    jmp .Lloop

.Lend:
    # If it's a negative number, negate the result
    cmpq $0, %r9
    je .Lfinal_negation_done
    neg %r10
.Lfinal_negation_done:
    # Restore stack registers and return the result
    popq %r12
    movq %rbp, %rsp
    popq %rbp
    movq %r10, %rax
    ret

.Lerror:
    # Write error message to stderr with syscall 'write'
    movq $1, %rax
    movq $2, %rdi
    movq $read_int_error_str, %rsi
    movq $read_int_error_str_len, %rdx
    syscall

    # Exit the program
    movq $60, %rax      # Syscall number for exit = 60.
    movq $1, %rdi       # Set exit code 1.
    syscall

read_int_error_str:
    .ascii "Error: read_int() failed to read input\\n"
read_int_error_str_len = . - read_int_error_str
"""
