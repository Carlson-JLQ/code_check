"""Subprocess adapter for building and running standalone CSA plugins."""

import os
import subprocess
from pathlib import Path


def _run(command, cwd=None, timeout=120):
    try:
        process = subprocess.run(
            [str(part) for part in command],
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", (exc.stderr or "") + "\ncommand timed out"
    except OSError as exc:
        return 127, "", str(exc)


def compile_csa_checker(
    cpp_path,
    workspace,
    llvm_root="/home/llvm/llvm-project",
    compiler=None,
    llvm_build="/home/checker/llvm-build",
    plugin_name=None,
    timeout=180,
):
    """Build a loadable analyzer plugin without changing the LLVM tree."""
    workspace = Path(workspace).resolve()
    cpp_path = Path(cpp_path).resolve()
    llvm_root = Path(llvm_root).resolve()
    llvm_build = Path(llvm_build).resolve()
    compiler = compiler or str(llvm_build / "bin/clang++")
    plugin = workspace / (plugin_name or f"{cpp_path.stem}.so")
    command = [
        compiler,
        "-std=c++17",
        "-fPIC",
        "-shared",
        "-fno-rtti",
        str(cpp_path),
        "-o",
        str(plugin),
        "-I",
        str(llvm_root / "llvm/include"),
        "-I",
        str(llvm_build / "include"),
        "-I",
        str(llvm_root / "clang/include"),
        "-I",
        str(llvm_build / "tools/clang/include"),
    ]
    rc, stdout, stderr = _run(command, cwd=workspace, timeout=timeout)
    return rc, stdout, stderr


def run_csa_analyzer(
    case_path,
    checker_name="gjb8114.NoAssignmentInCondition",
    analyzer=None,
    plugin_path=None,
    timeout=120,
    extra_args=None,
):
    analyzer = analyzer or "/home/checker/llvm-build/bin/clang"
    command = [analyzer, "--analyze", "-Wno-parentheses"]
    if plugin_path:
        command += ["-Xclang", "-load", "-Xclang", str(plugin_path)]
    command += [
        "-Xclang",
        "-analyzer-checker=" + checker_name,
        "-Xclang",
        "-analyzer-output=text",
    ]
    command += list(extra_args or [])
    command.append(str(case_path))
    return _run(command, timeout=timeout)


def validate_csa_environment(
    llvm_root="/home/llvm/llvm-project",
    llvm_build="/home/checker/llvm-build",
    compiler=None,
    analyzer=None,
):
    llvm_root, llvm_build = Path(llvm_root), Path(llvm_build)
    compiler = Path(compiler or llvm_build / "bin/clang++")
    analyzer = Path(analyzer or llvm_build / "bin/clang")
    checks = {
        "llvm_source": llvm_root / "llvm/include/llvm/Config/llvm-config.h.cmake",
        "clang_source_headers": llvm_root / "clang/include/clang/StaticAnalyzer/Core/Checker.h",
        "llvm_build_headers": llvm_build / "include/llvm/Config/llvm-config.h",
        "compiler": compiler,
        "analyzer": analyzer,
    }
    return {
        "success": all(path.exists() and (os.access(path, os.X_OK) if key in {"compiler", "analyzer"} else True)
                       for key, path in checks.items()),
        "paths": {key: str(path) for key, path in checks.items()},
        "missing": [key for key, path in checks.items() if not path.exists()],
    }
