#!/usr/bin/env python3
"""Statically extract Clang Static Analyzer APIs from official source files.

This script parses only the target .h and .cpp files with Tree-sitter. It does
not preprocess includes, configure LLVM, compile LLVM, or invoke CSA.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from tree_sitter import Language, Node, Parser
import tree_sitter_cpp


TYPE_NODES = {"class_specifier": "class", "struct_specifier": "struct"}
PUBLIC_HEADER_PREFIX = "clang/include/clang/StaticAnalyzer/"
DECLARATION_NODES = {"field_declaration", "declaration"}
PARAMETER_NODES = {
    "parameter_declaration",
    "optional_parameter_declaration",
    "variadic_parameter",
}
NAME_NODES = {
    "identifier",
    "field_identifier",
    "type_identifier",
    "qualified_identifier",
    "destructor_name",
    "operator_name",
    "conversion_function_id",
}
STORAGE_WORDS = {
    "explicit",
    "extern",
    "friend",
    "inline",
    "static",
    "virtual",
}


def load_cpp_language() -> Language:
    get_pointer = ctypes.pythonapi.PyCapsule_GetPointer
    get_pointer.restype = ctypes.c_void_p
    get_pointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
    pointer = get_pointer(tree_sitter_cpp.language(), b"tree_sitter.Language")
    return Language(pointer, "cpp")


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--llvm-root",
        type=Path,
        default=Path("/home/llvm/llvm-project"),
        help="LLVM monorepo source root",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=script_dir / "csa_api.json",
        help="Output JSON file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Parse only the first N files for a quick quality check",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the output JSON",
    )
    return parser.parse_args()


def text(node: Optional[Node], source: bytes) -> str:
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode(
        "utf-8", errors="replace"
    )


def normalize_space(value: str) -> str:
    return " ".join(value.strip().split())


def clean_comment(value: str) -> str:
    lines = []
    for raw_line in value.strip().splitlines():
        line = raw_line.strip()
        line = re.sub(r"^//[/!]?[<]?\s?", "", line)
        line = re.sub(r"^/\*+!?[<]?\s?", "", line)
        line = re.sub(r"\s?\*/$", "", line)
        line = re.sub(r"^\*\s?", "", line)
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def preceding_comment(node: Node, source: bytes) -> str:
    comments: list[str] = []
    previous = node.prev_named_sibling
    next_start_row = node.start_point[0]
    while previous and previous.type == "comment":
        if next_start_row - previous.end_point[0] > 2:
            break
        comments.append(text(previous, source))
        next_start_row = previous.start_point[0]
        previous = previous.prev_named_sibling
    comments.reverse()
    return clean_comment("\n".join(comments))


def source_record(node: Node, source: bytes, path: Path, llvm_root: Path) -> dict[str, Any]:
    return {
        "file": path.resolve().relative_to(llvm_root.resolve()).as_posix(),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "code": text(node, source).strip(),
    }


def stable_id(prefix: str, identity: str) -> str:
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{digest}"


def qualify(parts: Iterable[str]) -> str:
    return "::".join(part for part in parts if part)


def split_top_level(value: str, separator: str = ",") -> list[str]:
    result: list[str] = []
    start = 0
    depth = 0
    pairs = {"<": ">", "(": ")", "[": "]", "{": "}"}
    closers = set(pairs.values())
    for index, char in enumerate(value):
        if char in pairs:
            depth += 1
        elif char in closers:
            depth = max(0, depth - 1)
        elif char == separator and depth == 0:
            item = normalize_space(value[start:index])
            if item:
                result.append(item)
            start = index + 1
    tail = normalize_space(value[start:])
    if tail:
        result.append(tail)
    return result


def template_arguments(value: str) -> list[str]:
    start = value.find("<")
    end = value.rfind(">")
    if start < 0 or end <= start:
        return []
    return split_top_level(value[start + 1 : end])


def split_default(value: str) -> tuple[str, Optional[str]]:
    depth = 0
    for index, char in enumerate(value):
        if char in "<([{":
            depth += 1
        elif char in ">)]}":
            depth = max(0, depth - 1)
        elif char == "=" and depth == 0:
            return normalize_space(value[:index]), normalize_space(value[index + 1 :])
    return normalize_space(value), None


def parse_template_parameters(node: Optional[Node], source: bytes) -> list[dict[str, Any]]:
    if node is None:
        return []
    parameter_list = next(
        (child for child in node.named_children if child.type == "template_parameter_list"),
        None,
    )
    if parameter_list is None:
        return []
    raw = text(parameter_list, source).strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1]
    result = []
    for item in split_top_level(raw):
        declaration, default_value = split_default(item)
        is_type = bool(re.match(r"^(?:typename|class)\b", declaration))
        is_pack = "..." in declaration
        without_pack = declaration.replace("...", " ")
        words = re.findall(r"[A-Za-z_]\w*", without_pack)
        name = words[-1] if words else ""
        declared_type: Optional[str] = None
        if is_type:
            if name in {"typename", "class"}:
                name = ""
        else:
            name_match = re.search(r"([A-Za-z_]\w*)\s*$", without_pack)
            name = name_match.group(1) if name_match else ""
            declared_type = normalize_space(
                without_pack[: name_match.start()] if name_match else without_pack
            ) or None
        result.append(
            {
                "name": name,
                "kind": "type" if is_type else "non_type",
                "declared_type": declared_type,
                "is_pack": is_pack,
                "default_value": default_value,
            }
        )
    return result


def public_include(path: Path, llvm_root: Path) -> Optional[str]:
    relative = path.resolve().relative_to(llvm_root.resolve()).as_posix()
    if not relative.startswith(PUBLIC_HEADER_PREFIX) or path.suffix != ".h":
        return None
    return relative.removeprefix("clang/include/")


def mask_parser_directives(source: bytes) -> bytes:
    """Mask macro definitions and .def includes without changing byte offsets."""
    result = []
    in_define = False
    for line in source.splitlines(keepends=True):
        stripped = line.lstrip()
        should_mask = (
            in_define
            or stripped.startswith(b"#define")
            or (stripped.startswith(b"#include") and b".def" in stripped)
        )
        if should_mask:
            newline_size = 2 if line.endswith(b"\r\n") else 1 if line.endswith(b"\n") else 0
            result.append(b" " * (len(line) - newline_size) + line[len(line) - newline_size :])
        else:
            result.append(line)
        in_define = should_mask and line.rstrip(b"\r\n").endswith(b"\\")
    return b"".join(result)


def parse_bases(node: Node, source: bytes) -> list[dict[str, Any]]:
    clause = next(
        (child for child in node.named_children if child.type == "base_class_clause"),
        None,
    )
    if clause is None:
        return []
    raw = text(clause, source).strip().lstrip(":").strip()
    bases = []
    for item in split_top_level(raw):
        access_match = re.match(r"^(public|protected|private)\s+", item)
        access = access_match.group(1) if access_match else None
        spelling = re.sub(r"^(public|protected|private|virtual)\s+", "", item)
        spelling = re.sub(r"^(public|protected|private|virtual)\s+", "", spelling)
        base_name = spelling.split("<", 1)[0].strip()
        bases.append(
            {
                "name": base_name.split("::")[-1],
                "qualified_name": base_name,
                "spelling": spelling,
                "template_arguments": template_arguments(spelling),
                "access": access,
            }
        )
    return bases


def checker_callbacks(bases: Iterable[dict[str, Any]]) -> list[str]:
    callbacks: list[str] = []
    for base in bases:
        if base["name"] in {"Checker", "CheckerFamily"}:
            callbacks.extend(base["template_arguments"])
    return list(dict.fromkeys(callbacks))


def namespace_from_node(node: Node, source: bytes) -> str:
    name = node.child_by_field_name("name")
    return normalize_space(text(name, source)) if name else "(anonymous)"


def find_function_declarators(node: Node) -> list[Node]:
    result: list[Node] = []

    def visit(current: Node) -> None:
        if current.type == "function_declarator":
            ancestor = current.parent
            while ancestor and ancestor != node:
                if ancestor.type == "parenthesized_declarator":
                    return
                ancestor = ancestor.parent
            result.append(current)
            return
        if current.type in {"compound_statement", "lambda_expression"}:
            return
        for child in current.named_children:
            visit(child)

    visit(node)
    return result


def declarator_name_node(declarator: Optional[Node]) -> Optional[Node]:
    current = declarator
    while current is not None:
        if current.type in NAME_NODES:
            return current
        nested = current.child_by_field_name("declarator")
        if nested is not None:
            current = nested
            continue
        name = current.child_by_field_name("name")
        if name is not None:
            current = name
            continue
        candidates = [child for child in current.named_children if child.type in NAME_NODES]
        return candidates[-1] if candidates else None
    return None


def parameter_records(function_declarator: Node, source: bytes) -> list[dict[str, Any]]:
    parameter_list = function_declarator.child_by_field_name("parameters")
    if parameter_list is None:
        return []
    result = []
    for child in parameter_list.named_children:
        if child.type not in PARAMETER_NODES:
            continue
        if child.type == "variadic_parameter":
            result.append(
                {
                    "position": len(result),
                    "name": "",
                    "type": "...",
                    "canonical_type": None,
                    "default_value": None,
                }
            )
            continue
        declarator = child.child_by_field_name("declarator")
        name_node = declarator_name_node(declarator)
        default_node = child.child_by_field_name("default_value")
        type_end = default_node.start_byte if default_node else child.end_byte
        if name_node is not None:
            type_bytes = (
                source[child.start_byte : name_node.start_byte]
                + source[name_node.end_byte : type_end]
            )
            parameter_name = text(name_node, source)
        else:
            type_bytes = source[child.start_byte:type_end]
            parameter_name = ""
        parameter_type = normalize_space(
            type_bytes.decode("utf-8", errors="replace").rstrip(" =")
        )
        result.append(
            {
                "position": len(result),
                "name": parameter_name,
                "type": parameter_type,
                "canonical_type": None,
                "default_value": (
                    normalize_space(text(default_node, source)) if default_node else None
                ),
            }
        )
    return result


def function_signature(container: Node, source: bytes) -> str:
    body = container.child_by_field_name("body")
    end = body.start_byte if body else container.end_byte
    value = source[container.start_byte:end].decode("utf-8", errors="replace")
    return normalize_space(value.rstrip().rstrip(";"))


def templated_function_signature(
    container: Node, declaration_node: Node, source: bytes
) -> str:
    signature = function_signature(container, source)
    if declaration_node.type != "template_declaration":
        return signature
    prefix = source[declaration_node.start_byte : container.start_byte].decode(
        "utf-8", errors="replace"
    )
    return normalize_space(f"{prefix} {signature}")


def function_return_type(container: Node, name_node: Node, source: bytes) -> str:
    prefix = source[container.start_byte : name_node.start_byte].decode(
        "utf-8", errors="replace"
    )
    prefix = re.sub(r"template\s*<.*?>\s*", "", prefix, flags=re.DOTALL)
    words = normalize_space(prefix).split()
    words = [word for word in words if word not in STORAGE_WORDS]
    return normalize_space(" ".join(words))


def callable_qualifiers(container: Node, function_declarator: Node, source: bytes) -> dict[str, bool]:
    declaration = function_signature(container, source)
    declarator_text = normalize_space(text(function_declarator, source))
    suffix = declarator_text[declarator_text.rfind(")") + 1 :]
    return {
        "const": bool(re.search(r"\bconst\b", suffix)),
        "static": bool(re.search(r"\bstatic\b", declaration)),
        "virtual": bool(re.search(r"\bvirtual\b", declaration)),
        "pure_virtual": bool(re.search(r"=\s*0\s*$", declaration)),
        "override": bool(re.search(r"\boverride\b", suffix)),
        "noexcept": bool(re.search(r"\bnoexcept\b", suffix)),
    }


class CSAApiCollector:
    def __init__(self, llvm_root: Path) -> None:
        self.llvm_root = llvm_root.resolve()
        self.parser = Parser()
        self.parser.set_language(load_cpp_language())
        self.types: dict[str, dict[str, Any]] = {}
        self.type_by_suffix: dict[str, list[str]] = {}
        self.apis: dict[str, dict[str, Any]] = {}
        self.stats: Counter[str] = Counter()

    def parse_file(self, path: Path) -> None:
        source = path.read_bytes()
        tree = self.parser.parse(mask_parser_directives(source))
        if tree.root_node.has_error:
            self.stats["files_with_syntax_errors"] += 1
        self.collect_types(tree.root_node, source, path, [], [], None, None)
        self.collect_callables(tree.root_node, source, path, [], None, None, None)
        self.stats["parsed_files"] += 1

    def collect_types(
        self,
        node: Node,
        source: bytes,
        path: Path,
        namespaces: list[str],
        owners: list[str],
        access: Optional[str],
        template_node: Optional[Node],
    ) -> None:
        if node.type == "namespace_definition":
            namespace = namespace_from_node(node, source)
            body = node.child_by_field_name("body")
            if body:
                self.collect_types(
                    body, source, path, namespaces + [namespace], owners, access, None
                )
            return
        if node.type == "template_declaration":
            declaration = node.named_children[-1] if node.named_children else None
            if declaration is not None:
                self.collect_types(
                    declaration, source, path, namespaces, owners, access, node
                )
            return
        if node.type in TYPE_NODES:
            name_node = node.child_by_field_name("name")
            if name_node is None:
                return
            name = normalize_space(text(name_node, source))
            qualified_name = qualify([*namespaces, *owners, name])
            identity = qualified_name
            if "(anonymous)" in qualified_name:
                identity += f"|{path}:{node.start_point[0] + 1}"
            type_id = stable_id("type", identity)
            bases = parse_bases(node, source)
            declaration_node = template_node or node
            include = public_include(path, self.llvm_root)
            eligible = bool(
                include
                and "(anonymous)" not in namespaces
                and access not in {"private", "protected"}
            )
            record = {
                "id": type_id,
                "kind": TYPE_NODES[node.type],
                "name": name,
                "qualified_name": qualified_name,
                "namespace": qualify(namespaces),
                "bases": bases,
                "template_parameters": parse_template_parameters(template_node, source),
                "callbacks": checker_callbacks(bases),
                "owner_id": self.find_owner_id(owners, namespaces),
                "owner_name": qualify([*namespaces, *owners]) if owners else None,
                "access": access,
                "availability": "public_framework",
                "reusable": True,
                "required_includes": [include] if include else [],
                "comment": preceding_comment(declaration_node, source),
                "source": source_record(
                    declaration_node, source, path, self.llvm_root
                ),
                "_eligible": eligible,
            }
            current = self.types.get(type_id)
            if current is None or (
                record["_eligible"] and not current["_eligible"]
            ) or (
                record["_eligible"] == current["_eligible"]
                and len(record["source"]["code"]) > len(current["source"]["code"])
            ):
                self.types[type_id] = record
            if type_id not in self.type_by_suffix.setdefault(name, []):
                self.type_by_suffix[name].append(type_id)
            body = node.child_by_field_name("body")
            if body:
                current_access = "private" if node.type == "class_specifier" else "public"
                for child in body.named_children:
                    if child.type == "access_specifier":
                        current_access = text(child, source).strip().rstrip(":")
                        continue
                    self.collect_types(
                        child,
                        source,
                        path,
                        namespaces,
                        owners + [name],
                        current_access,
                        None,
                    )
            return
        if node.type == "enum_specifier":
            self.add_enum(
                node, template_node or node, source, path, namespaces, owners, access
            )
            return
        if node.type in {"alias_declaration", "type_definition"}:
            self.add_alias(
                node, template_node or node, source, path, namespaces, owners, access
            )
            return
        if node.type == "function_definition":
            return
        for child in node.named_children:
            self.collect_types(child, source, path, namespaces, owners, access, None)

    def find_owner_id(self, owners: list[str], namespaces: list[str]) -> Optional[str]:
        if not owners:
            return None
        qualified_name = qualify([*namespaces, *owners])
        return stable_id("type", qualified_name)

    def common_type_fields(
        self,
        node: Node,
        declaration_node: Node,
        source: bytes,
        path: Path,
        namespaces: list[str],
        owners: list[str],
        access: Optional[str],
    ) -> tuple[Optional[str], bool, dict[str, Any]]:
        include = public_include(path, self.llvm_root)
        eligible = bool(
            include
            and "(anonymous)" not in namespaces
            and access not in {"private", "protected"}
        )
        return include, eligible, {
            "namespace": qualify(namespaces),
            "owner_id": self.find_owner_id(owners, namespaces),
            "owner_name": qualify([*namespaces, *owners]) if owners else None,
            "access": access,
            "availability": "public_framework",
            "reusable": True,
            "required_includes": [include] if include else [],
            "comment": preceding_comment(declaration_node, source),
            "source": source_record(declaration_node, source, path, self.llvm_root),
            "_eligible": eligible,
        }

    def add_enum(
        self,
        node: Node,
        declaration_node: Node,
        source: bytes,
        path: Path,
        namespaces: list[str],
        owners: list[str],
        access: Optional[str],
    ) -> None:
        name_node = node.child_by_field_name("name")
        name = normalize_space(text(name_node, source)) if name_node else ""
        relative = path.resolve().relative_to(self.llvm_root).as_posix()
        location_identity = f"{relative}:{node.start_point[0] + 1}"
        display_name = name or f"(anonymous enum at {location_identity})"
        qualified_name = qualify([*namespaces, *owners, display_name])
        enum_id = stable_id("type", qualified_name if name else location_identity)
        raw = text(node, source)
        header = raw.split("{", 1)[0]
        scoped = bool(re.match(r"\s*enum\s+(?:class|struct)\b", header))
        underlying_type = None
        underlying_node = node.child_by_field_name("underlying_type")
        if underlying_node is not None:
            underlying_type = normalize_space(text(underlying_node, source)).lstrip(": ")
        elif ":" in header:
            underlying_type = normalize_space(header.rsplit(":", 1)[1]) or None
        body = node.child_by_field_name("body")
        enumerators = []
        if body is not None:
            for item in body.named_children:
                if item.type != "enumerator":
                    continue
                item_name_node = item.child_by_field_name("name")
                item_name = normalize_space(text(item_name_node, source))
                value_node = item.child_by_field_name("value")
                if value_node is None:
                    value_node = next(
                        (child for child in item.named_children if child != item_name_node),
                        None,
                    )
                enumerators.append(
                    {
                        "name": item_name,
                        "qualified_name": f"{qualified_name}::{item_name}",
                        "value": normalize_space(text(value_node, source)) or None,
                        "comment": preceding_comment(item, source),
                        "source": source_record(item, source, path, self.llvm_root),
                    }
                )
        _, _, common = self.common_type_fields(
            node, declaration_node, source, path, namespaces, owners, access
        )
        record = {
            "id": enum_id,
            "kind": "enum",
            "name": name,
            "qualified_name": qualified_name,
            "scoped": scoped,
            "underlying_type": underlying_type,
            "enumerators": enumerators,
            "template_parameters": [],
            **common,
        }
        self.types[enum_id] = record

    def add_alias(
        self,
        node: Node,
        declaration_node: Node,
        source: bytes,
        path: Path,
        namespaces: list[str],
        owners: list[str],
        access: Optional[str],
    ) -> None:
        name_node = (
            node.child_by_field_name("name")
            if node.type == "alias_declaration"
            else node.child_by_field_name("declarator")
        )
        if name_node is None:
            return
        name = normalize_space(text(name_node, source))
        qualified_name = qualify([*namespaces, *owners, name])
        target_node = node.child_by_field_name("type")
        target_type = normalize_space(text(target_node, source))
        _, _, common = self.common_type_fields(
            node, declaration_node, source, path, namespaces, owners, access
        )
        alias_id = stable_id("type", qualified_name)
        self.types[alias_id] = {
            "id": alias_id,
            "kind": "type_alias",
            "name": name,
            "qualified_name": qualified_name,
            "alias_syntax": "using" if node.type == "alias_declaration" else "typedef",
            "target_type": target_type,
            "template_parameters": parse_template_parameters(
                declaration_node if declaration_node.type == "template_declaration" else None,
                source,
            ),
            **common,
        }

    def collect_callables(
        self,
        node: Node,
        source: bytes,
        path: Path,
        namespaces: list[str],
        owner_id: Optional[str],
        access: Optional[str],
        template_node: Optional[Node],
    ) -> Optional[str]:
        if node.type == "namespace_definition":
            namespace = namespace_from_node(node, source)
            body = node.child_by_field_name("body")
            if body:
                self.collect_callables(
                    body, source, path, namespaces + [namespace], owner_id, access, None
                )
            return access
        if node.type == "template_declaration":
            declaration = node.named_children[-1] if node.named_children else None
            if declaration is not None:
                self.collect_callables(
                    declaration,
                    source,
                    path,
                    namespaces,
                    owner_id,
                    access,
                    node,
                )
            return access
        if node.type in TYPE_NODES:
            name_node = node.child_by_field_name("name")
            if name_node is None:
                return access
            name = normalize_space(text(name_node, source))
            matched_owner = self.find_type_id(name, namespaces, path, node)
            body = node.child_by_field_name("body")
            if body and matched_owner:
                current_access = "private" if node.type == "class_specifier" else "public"
                for child in body.named_children:
                    if child.type == "access_specifier":
                        current_access = text(child, source).strip().rstrip(":")
                        continue
                    self.collect_callables(
                        child,
                        source,
                        path,
                        namespaces,
                        matched_owner,
                        current_access,
                        None,
                    )
            return access
        if node.type == "function_definition":
            self.add_callables(
                node, template_node or node, source, path, namespaces, owner_id, access, True
            )
            return access
        if node.type in DECLARATION_NODES:
            self.add_callables(
                node, template_node or node, source, path, namespaces, owner_id, access, False
            )
            return access
        if node.type == "compound_statement":
            return access
        for child in node.named_children:
            self.collect_callables(
                child, source, path, namespaces, owner_id, access, None
            )
        return access

    def find_type_id(
        self,
        name: str,
        namespaces: list[str],
        path: Path,
        node: Node,
    ) -> Optional[str]:
        qualified_name = qualify([*namespaces, name])
        candidates = self.type_by_suffix.get(name, [])
        for type_id in candidates:
            if self.types[type_id]["qualified_name"] == qualified_name:
                return type_id
        for type_id in candidates:
            source = self.types[type_id]["source"]
            if source["file"] == path.relative_to(self.llvm_root).as_posix():
                return type_id
        return candidates[0] if len(candidates) == 1 else None

    def infer_owner(self, raw_name: str, path: Path) -> Optional[str]:
        if "::" not in raw_name:
            return None
        owner_name = raw_name.rsplit("::", 1)[0].split("::")[-1]
        candidates = self.type_by_suffix.get(owner_name, [])
        same_file = [
            type_id
            for type_id in candidates
            if self.types[type_id]["source"]["file"]
            == path.relative_to(self.llvm_root).as_posix()
        ]
        if len(same_file) == 1:
            return same_file[0]
        return candidates[0] if len(candidates) == 1 else None

    def add_callables(
        self,
        container: Node,
        declaration_node: Node,
        source: bytes,
        path: Path,
        namespaces: list[str],
        owner_id: Optional[str],
        access: Optional[str],
        is_definition: bool,
    ) -> None:
        for declarator in find_function_declarators(container):
            name_node = declarator_name_node(declarator.child_by_field_name("declarator"))
            if name_node is None:
                continue
            raw_name = normalize_space(text(name_node, source)).lstrip(":")
            if raw_name.startswith("ento::"):
                raw_name = f"clang::{raw_name}"
            short_name = raw_name.rsplit("::", 1)[-1]
            resolved_owner = owner_id or self.infer_owner(raw_name, path)
            owner = self.types.get(resolved_owner) if resolved_owner else None
            if owner:
                qualified_name = f"{owner['qualified_name']}::{short_name}"
            else:
                qualified_name = qualify([*namespaces, raw_name])
            parameters = parameter_records(declarator, source)
            if owner is None and "::" in raw_name:
                parameter_types = [item["type"] for item in parameters]
                matches = [
                    item
                    for item in self.apis.values()
                    if item["qualified_name"].endswith(f"::{raw_name}")
                    and [parameter["type"] for parameter in item["parameters"]]
                    == parameter_types
                ]
                if len(matches) == 1:
                    qualified_name = matches[0]["qualified_name"]
            qualifiers = callable_qualifiers(container, declarator, source)
            parameter_key = ",".join(item["type"] for item in parameters)
            identity = f"{qualified_name}({parameter_key})"
            if qualifiers["const"]:
                identity += " const"
            api_id = stable_id("api", identity)

            owner_name = owner["qualified_name"] if owner else None
            if owner and short_name == owner["name"]:
                kind = "constructor"
                return_type = ""
            elif owner and short_name == f"~{owner['name']}":
                kind = "destructor"
                return_type = ""
            else:
                kind = "method" if owner else "function"
                return_type = function_return_type(container, name_node, source)

            category = self.classify(short_name, owner, path)
            record = self.apis.get(api_id)
            include = public_include(path, self.llvm_root)
            eligible = bool(
                include
                and "(anonymous)" not in namespaces
                and access not in {"private", "protected"}
                and (owner is None or owner.get("_eligible", False))
            )
            if record is None:
                record = {
                    "id": api_id,
                    "kind": kind,
                    "name": short_name,
                    "qualified_name": qualified_name,
                    "namespace": qualify(namespaces),
                    "owner_id": resolved_owner,
                    "owner_name": owner_name,
                    "signature": templated_function_signature(
                        container, declaration_node, source
                    ),
                    "return_type": return_type,
                    "parameters": parameters,
                    "template_parameters": parse_template_parameters(
                        declaration_node
                        if declaration_node.type == "template_declaration"
                        else None,
                        source,
                    ),
                    "access": access,
                    "qualifiers": qualifiers,
                    "category": category,
                    "callbacks": owner["callbacks"] if owner else [],
                    "comment": preceding_comment(declaration_node, source),
                    "declarations": [],
                    "definition": None,
                    "availability": "public_framework",
                    "reusable": True,
                    "required_includes": [include] if include else [],
                    "_eligible": eligible,
                }
                self.apis[api_id] = record
            elif eligible:
                record["_eligible"] = True
                record["required_includes"] = [include]
                record["access"] = access
                record["template_parameters"] = parse_template_parameters(
                    declaration_node
                    if declaration_node.type == "template_declaration"
                    else None,
                    source,
                )

            location = source_record(declaration_node, source, path, self.llvm_root)
            if is_definition:
                record["definition"] = {
                    "source_type": path.suffix.lstrip("."),
                    **location,
                }
            elif not any(
                declaration["file"] == location["file"]
                and declaration["start_line"] == location["start_line"]
                for declaration in record["declarations"]
            ):
                record["declarations"].append(location)

    @staticmethod
    def classify(short_name: str, owner: Optional[dict[str, Any]], path: Path) -> str:
        if short_name.startswith("register") or short_name.startswith("shouldRegister"):
            return "registration"
        if owner and owner["callbacks"]:
            expected_methods = set()
            for callback in owner["callbacks"]:
                callback_name = callback.split("<", 1)[0]
                if "::" not in callback_name:
                    continue
                scope, event = callback_name.rsplit("::", 1)
                prefix = "eval" if scope.endswith("eval") else "check"
                expected_methods.add(f"{prefix}{event}")
            if short_name in expected_methods:
                return "checker_callback"
            return "checker_helper"
        if "/lib/StaticAnalyzer/Checkers/" in path.as_posix():
            return "utility"
        return "framework_api"

    def result(self) -> dict[str, Any]:
        candidate_types = []
        for record in self.types.values():
            if record.pop("_eligible", False):
                candidate_types.append(record)
            else:
                self.count_exclusion(record)
        candidate_type_ids = {record["id"] for record in candidate_types}
        while True:
            inaccessible = {
                record["id"]
                for record in candidate_types
                if record["id"] in candidate_type_ids
                and record["owner_id"] is not None
                and record["owner_id"] not in candidate_type_ids
            }
            if not inaccessible:
                break
            candidate_type_ids.difference_update(inaccessible)
        included_types = [
            record for record in candidate_types if record["id"] in candidate_type_ids
        ]
        self.stats["excluded_inaccessible_owner"] += len(
            candidate_types
        ) - len(included_types)
        included_type_ids = {record["id"] for record in included_types}
        included_apis = []
        for record in self.apis.values():
            eligible = record.pop("_eligible", False)
            if eligible and (record["owner_id"] is None or record["owner_id"] in included_type_ids):
                included_apis.append(record)
            else:
                self.count_exclusion(record)
        return {
            "types": sorted(included_types, key=lambda item: item["qualified_name"]),
            "apis": sorted(included_apis, key=lambda item: item["qualified_name"]),
        }

    def count_exclusion(self, record: dict[str, Any]) -> None:
        source = record.get("source")
        if source is None:
            declarations = record.get("declarations", [])
            source = declarations[0] if declarations else record.get("definition")
        file_name = source.get("file", "") if source else ""
        if "(anonymous)" in record.get("namespace", ""):
            reason = "anonymous_namespace"
        elif record.get("access") in {"private", "protected"}:
            reason = f"{record['access']}_member"
        elif file_name.endswith(".cpp"):
            reason = "cpp_only"
        elif file_name.startswith("clang/lib/"):
            reason = "internal_header"
        else:
            reason = "not_publicly_reusable"
        self.stats[f"excluded_{reason}"] += 1


def input_files(llvm_root: Path) -> list[Path]:
    framework_root = llvm_root / "clang/include/clang/StaticAnalyzer"
    checker_root = llvm_root / "clang/lib/StaticAnalyzer/Checkers"
    missing = [str(root) for root in (framework_root, checker_root) if not root.is_dir()]
    if missing:
        raise SystemExit(f"Missing input directories: {', '.join(missing)}")
    files = list(framework_root.rglob("*.h"))
    files.extend(checker_root.rglob("*.h"))
    files.extend(checker_root.rglob("*.cpp"))
    return sorted(set(path.resolve() for path in files))


def git_revision(llvm_root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(llvm_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> int:
    args = parse_args()
    llvm_root = args.llvm_root.resolve()
    files = input_files(llvm_root)
    if args.limit is not None:
        files = files[: args.limit]

    collector = CSAApiCollector(llvm_root)
    for index, path in enumerate(files, start=1):
        relative_path = path.relative_to(llvm_root).as_posix()
        print(f"[{index}/{len(files)}] {relative_path}")
        collector.parse_file(path)

    extracted = collector.result()
    excluded_counts = {
        key.removeprefix("excluded_"): value
        for key, value in sorted(collector.stats.items())
        if key.startswith("excluded_")
    }
    result = {
        "metadata": {
            "schema_version": "1.1",
            "input_policy": "public_reusable_only",
            "parser": "tree-sitter-cpp",
            "llvm_root": str(llvm_root),
            "llvm_revision": git_revision(llvm_root),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_roots": [
                "clang/include/clang/StaticAnalyzer",
                "clang/lib/StaticAnalyzer/Checkers",
            ],
            "parsed_files": collector.stats["parsed_files"],
            "files_with_syntax_errors": collector.stats["files_with_syntax_errors"],
            "excluded_counts": excluded_counts,
        },
        **extracted,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output_file:
        json.dump(result, output_file, ensure_ascii=False, indent=2 if args.pretty else None)
        output_file.write("\n")
    print(f"Saved {len(result['types'])} types and {len(result['apis'])} APIs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
