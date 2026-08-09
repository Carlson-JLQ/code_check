"""Tree-sitter inventory pass used before semantic checker decomposition."""

from __future__ import annotations

import ctypes
import re
from pathlib import Path
from typing import Any, Iterator

from tree_sitter import Language, Node, Parser
import tree_sitter_cpp


CHECKER_ROOT = Path("clang/lib/StaticAnalyzer/Checkers")


def load_cpp_language() -> Language:
    get_pointer = ctypes.pythonapi.PyCapsule_GetPointer
    get_pointer.restype = ctypes.c_void_p
    get_pointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
    pointer = get_pointer(tree_sitter_cpp.language(), b"tree_sitter.Language")
    return Language(pointer, "cpp")


def walk(node: Node) -> Iterator[Node]:
    yield node
    for child in node.named_children:
        yield from walk(child)


def node_text(node: Node | None, source: bytes) -> str:
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def event_method(event: str) -> str:
    stem = event.split("<", 1)[0]
    namespace, _, name = stem.partition("::")
    if namespace == "check":
        return "check" + name
    if namespace == "eval":
        return "eval" + name
    return name


class StaticAnalyzer:
    """Collect syntax-backed checker classes, functions, and local call edges."""

    def __init__(self, llvm_root: Path):
        self.llvm_root = llvm_root.resolve()
        self.checker_root = self.llvm_root / CHECKER_ROOT
        self.parser = Parser()
        self.parser.set_language(load_cpp_language())

    def analyze_file(self, path: Path) -> dict[str, Any]:
        source = path.read_bytes()
        tree = self.parser.parse(source)
        relative = path.resolve().relative_to(self.llvm_root).as_posix()
        classes, functions = [], []
        for node in walk(tree.root_node):
            if node.type == "class_specifier":
                raw = node_text(node, source)
                header = raw.split("{", 1)[0]
                if not re.search(r"\bChecker(?:Family)?\s*<", header):
                    continue
                name = node_text(node.child_by_field_name("name"), source)
                match = re.search(r"\bChecker(?:Family)?\s*<(.+)", header, re.S)
                event_text = match.group(1).rsplit(">", 1)[0] if match else ""
                events = self._split_template_args(event_text)
                classes.append({
                    "implementation_class": name,
                    "events": events,
                    "callbacks": [{"event": event, "method": f"{name}::{event_method(event)}"} for event in events],
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                })
            elif node.type == "function_definition":
                declarator = node.child_by_field_name("declarator")
                signature = node_text(declarator, source)
                match = re.search(r"([A-Za-z_]\w*(?:::[~A-Za-z_]\w*)+)\s*\(", signature)
                if not match:
                    continue
                symbol = match.group(1)
                body = node.child_by_field_name("body")
                calls = []
                if body is not None:
                    for descendant in walk(body):
                        if descendant.type != "call_expression":
                            continue
                        called = node_text(descendant.child_by_field_name("function"), source).strip()
                        if called and called not in calls:
                            calls.append(called)
                functions.append({
                    "symbol": symbol,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "calls": calls,
                })
        decoded = source.decode("utf-8", errors="replace")
        traits = []
        macro_pattern = re.compile(
            r"REGISTER_(MAP|SET|LIST|TRAIT)(?:_FACTORY)?_WITH_PROGRAMSTATE\s*"
            r"\(\s*([A-Za-z_]\w*)\s*(?:,\s*([^,\n)]+))?\s*(?:,\s*([^\n)]+))?\)"
        )
        for match in macro_pattern.finditer(decoded):
            traits.append({
                "name": match.group(2),
                "kind": match.group(1).lower(),
                "key_type": match.group(3).strip() if match.group(3) else None,
                "value_type": match.group(4).strip() if match.group(4) else None,
                "line": decoded.count("\n", 0, match.start()) + 1,
            })
        headers = []
        for include in re.findall(r'^\s*#include\s+"([^"]+\.h)"', decoded, re.M):
            candidate = self.checker_root / Path(include).name
            if candidate.is_file() and candidate.resolve() != path.resolve():
                headers.append(candidate.resolve().relative_to(self.llvm_root).as_posix())
        return {
            "file": relative,
            "has_syntax_error": tree.root_node.has_error,
            "direct_checker_headers": sorted(set(headers)),
            "checker_classes": classes,
            "functions": functions,
            "state_traits": traits,
            "registrations": self._registrations(decoded),
        }

    @staticmethod
    def _split_template_args(value: str) -> list[str]:
        result, start, depth = [], 0, 0
        for index, char in enumerate(value):
            if char == "<":
                depth += 1
            elif char == ">":
                depth -= 1
            elif char == "," and depth == 0:
                result.append(" ".join(value[start:index].split()))
                start = index + 1
        tail = " ".join(value[start:].split())
        if tail:
            result.append(tail)
        return result

    @staticmethod
    def _registrations(source: str) -> list[dict[str, Any]]:
        result = []
        pattern = re.compile(r"void\s+ento::register([A-Za-z_]\w*)\s*\([^)]*\)\s*\{(.*?)\n\}", re.S)
        for match in pattern.finditer(source):
            name, body = match.group(1), match.group(2)
            backend = re.search(r"(?:getChecker|registerChecker)<([A-Za-z_]\w*)>", body)
            member = re.search(r"->([A-Za-z_]\w*)\.enable\s*\(", body)
            result.append({
                "name": name.removesuffix("Checker"),
                "registration_function": f"ento::register{name}",
                "implementation_class": backend.group(1) if backend else None,
                "frontend_member": member.group(1) if member else None,
            })
        for match in re.finditer(r"^REGISTER_CHECKER\(([A-Za-z_]\w*)\)", source, re.M):
            member = match.group(1)
            result.append({
                "name": member.removesuffix("Checker"),
                "registration_function": f"ento::register{member}",
                "implementation_class": "MallocChecker",
                "frontend_member": member,
            })
        return result

    def callback_slices(self, inventory: dict[str, Any]) -> list[dict[str, Any]]:
        functions = {item["symbol"]: item for item in inventory["functions"]}
        short_names = {symbol.rsplit("::", 1)[-1]: symbol for symbol in functions}
        slices = []
        for checker in inventory["checker_classes"]:
            for callback in checker["callbacks"]:
                root = callback["method"]
                if root not in functions:
                    continue
                ordered, seen = [], set()

                def visit(symbol: str) -> None:
                    if symbol in seen:
                        return
                    seen.add(symbol)
                    ordered.append(symbol)
                    for call in functions[symbol]["calls"]:
                        target = short_names.get(call.rsplit("::", 1)[-1])
                        if target:
                            visit(target)

                visit(root)
                slices.append({"callback": callback, "symbols_in_call_order": ordered})
        return slices


def scan_checker_sources(llvm_root: Path, names: set[str] | None = None) -> dict[str, Any]:
    analyzer = StaticAnalyzer(llvm_root)
    files = []
    for path in sorted(analyzer.checker_root.glob("*.cpp")):
        inventory = analyzer.analyze_file(path)
        classes = {item["implementation_class"] for item in inventory["checker_classes"]}
        if names and not classes.intersection(names):
            continue
        inventory["callback_slices"] = analyzer.callback_slices(inventory)
        files.append(inventory)
    return {"source_root": CHECKER_ROOT.as_posix(), "files": files}

