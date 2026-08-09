#!/usr/bin/env python3
"""Build and validate the Stage 2 CSA checker logic dataset.

The canonical JSON stays grouped by implementation class.  Semantic plans only
select source ranges; this collector always reconstructs ``meta_impl`` from the
LLVM source tree and resolves API IDs against the independent Stage 1 dataset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from .static_analysis import scan_checker_sources
except ImportError:  # Direct script execution.
    from static_analysis import scan_checker_sources


KINDS = {
    "entry_filter",
    "value_modeling",
    "state_modeling",
    "constraint_reasoning",
    "detection",
    "state_transition",
    "reporting",
    "lifecycle_cleanup",
    "escape_handling",
    "utility",
}
BEHAVIOR_FIELDS = (
    "preconditions",
    "state_reads",
    "state_writes",
    "transitions",
    "reports",
)
SOURCE_ROOT = "clang/lib/StaticAnalyzer/Checkers"


def stable_id(prefix: str, identity: str) -> str:
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{digest}"


def git_revision(root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


@dataclass(frozen=True)
class SegmentSpec:
    symbol: str
    start: str
    end: str
    role: str = "callback_segment"
    occurrence: int = 1


class SourceIndex:
    """Line-oriented exact source slicer with symbol-boundary checks."""

    def __init__(self, llvm_root: Path):
        self.llvm_root = llvm_root.resolve()
        self._lines: dict[str, list[str]] = {}

    def lines(self, relative: str) -> list[str]:
        if relative not in self._lines:
            path = self.llvm_root / relative
            self._lines[relative] = path.read_text(encoding="utf-8").splitlines()
        return self._lines[relative]

    @staticmethod
    def _matches(lines: list[str], marker: str) -> list[int]:
        return [index for index, line in enumerate(lines) if marker in line]

    def span(self, relative: str, spec: SegmentSpec) -> tuple[dict[str, Any], str]:
        lines = self.lines(relative)
        starts = self._matches(lines, spec.start)
        if len(starts) < spec.occurrence:
            raise ValueError(f"source marker not found: {relative}: {spec.start!r}")
        start = starts[spec.occurrence - 1]
        ends = [i for i in self._matches(lines, spec.end) if i >= start]
        if not ends:
            raise ValueError(f"end marker not found: {relative}: {spec.end!r}")
        end = ends[0]
        code = "\n".join(lines[start : end + 1])
        return (
            {
                "role": spec.role,
                "symbol": spec.symbol,
                "file": relative,
                "start_line": start + 1,
                "end_line": end + 1,
            },
            code,
        )

    def exact_text(self, span: dict[str, Any]) -> str:
        lines = self.lines(span["file"])
        return "\n".join(lines[span["start_line"] - 1 : span["end_line"]])


class ApiIndex:
    def __init__(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.ids = {item["id"] for item in data.get("apis", [])}
        self.by_name: dict[str, list[dict[str, Any]]] = {}
        for item in data.get("apis", []):
            self.by_name.setdefault(item["qualified_name"], []).append(item)

    def refs(self, qualified_names: Iterable[str], *, strict: bool = False) -> list[dict[str, str]]:
        result = []
        for name in qualified_names:
            matches = self.by_name.get(name, [])
            if matches:
                # Overloads share a name. The stable first record is sufficient
                # unless a semantic plan supplies a full signature in future.
                item = sorted(matches, key=lambda record: record["id"])[0]
                result.append({"id": item["id"], "qualified_name": name})
            elif strict:
                raise ValueError(f"qualified API name absent from Stage 1: {name}")
        return result


def behavior(**values: list[str]) -> dict[str, list[str]]:
    return {field: list(values.get(field, [])) for field in BEHAVIOR_FIELDS}


def frontend(checker: str, name: str, registration: str, member: str | None) -> dict[str, Any]:
    identity = f"{checker}:{name}:{registration}"
    return {
        "id": stable_id("frontend", identity),
        "name": name,
        "registration_function": registration,
        "frontend_member": member,
    }


def unit(
    slug: str,
    kind: str,
    meta_op: str,
    segments: list[SegmentSpec],
    *,
    callbacks: list[str],
    frontends: list[str] | None = None,
    depends: list[str] | None = None,
    api_names: list[str] | None = None,
    effects: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "kind": kind,
        "meta_op": meta_op,
        "segments": segments,
        "callback_context": callbacks,
        "frontends": frontends,
        "depends": depends or [],
        "api_names": api_names or [],
        "behavior": effects or behavior(),
    }


def representative_specs() -> list[dict[str, Any]]:
    """Reviewed semantic plans for the three Stage 2 acceptance checkers."""
    div_file = f"{SOURCE_ROOT}/DivZeroChecker.cpp"
    div_frontends = [
        frontend("DivZeroChecker", "DivZero", "ento::registerDivZeroChecker", "DivideZeroChecker"),
        frontend("DivZeroChecker", "TaintedDiv", "ento::registerTaintedDivChecker", "TaintedDivChecker"),
    ]
    div_ids = [item["id"] for item in div_frontends]
    div = {
        "implementation_class": "DivZeroChecker",
        "summary": "Detect definite and tainted division by zero.",
        "analysis_mode": "path_sensitive",
        "source_files": [div_file],
        "callbacks": [{"event": "check::PreStmt<BinaryOperator>", "method": "DivZeroChecker::checkPreStmt"}],
        "frontends": div_frontends,
        "state_traits": [],
        "units": [
            unit("entry-filter", "entry_filter", "Restrict analysis to scalar division and remainder operations.", [SegmentSpec("DivZeroChecker::checkPreStmt", "BinaryOperator::Opcode Op", "if (!B->getRHS()->getType()->isScalarType())") , SegmentSpec("DivZeroChecker::checkPreStmt", "if (!B->getRHS()->getType()->isScalarType())", "return;")], callbacks=["DivZeroChecker::checkPreStmt"], frontends=div_ids, effects=behavior(preconditions=["operator is division or remainder", "denominator type is scalar"])),
            unit("denominator-value", "value_modeling", "Read the denominator symbolic value and require it to be defined.", [SegmentSpec("DivZeroChecker::checkPreStmt", "SVal Denom =", "if (!DV)"), SegmentSpec("DivZeroChecker::checkPreStmt", "if (!DV)", "return;")], callbacks=["DivZeroChecker::checkPreStmt"], frontends=div_ids, depends=["entry-filter"], api_names=["clang::ento::CheckerContext::getSVal"]),
            unit("zero-constraints", "constraint_reasoning", "Split the current path into non-zero and zero denominator states.", [SegmentSpec("DivZeroChecker::checkPreStmt", "ConstraintManager &CM", "CM.assumeDual")], callbacks=["DivZeroChecker::checkPreStmt"], frontends=div_ids, depends=["denominator-value"], api_names=["clang::ento::CheckerContext::getConstraintManager", "clang::ento::CheckerContext::getState", "clang::ento::ConstraintManager::assumeDual"], effects=behavior(state_reads=["current ProgramState"], transitions=["stateNotZero", "stateZero"])),
            unit("definite-zero-report", "reporting", "Report definite division by zero when the non-zero branch is infeasible.", [SegmentSpec("DivZeroChecker::checkPreStmt", "if (!stateNotZero)", "return;"), SegmentSpec("DivZeroChecker::reportBug", "void DivZeroChecker::reportBug", "}" , "helper", 1)], callbacks=["DivZeroChecker::checkPreStmt"], frontends=[div_ids[0]], depends=["zero-constraints"], api_names=["clang::ento::CheckerContext::generateErrorNode", "clang::ento::CheckerContext::emitReport"], effects=behavior(preconditions=["stateNotZero is infeasible"], reports=["Division by zero"])),
            unit("tainted-zero-report", "reporting", "Report a possibly-zero denominator when both branches are feasible and the value is tainted.", [SegmentSpec("DivZeroChecker::checkPreStmt", "if ((stateNotZero && stateZero))", "}"), SegmentSpec("DivZeroChecker::reportTaintBug", "void DivZeroChecker::reportTaintBug", "}" , "helper", 1)], callbacks=["DivZeroChecker::checkPreStmt"], frontends=[div_ids[1]], depends=["zero-constraints"], api_names=["clang::ento::CheckerContext::generateErrorNode", "clang::ento::CheckerContext::emitReport"], effects=behavior(preconditions=["zero and non-zero states are feasible", "denominator is tainted"], reports=["Division by a tainted value, possibly zero"])),
            unit("nonzero-transition", "state_transition", "Continue analysis only with the non-zero denominator state.", [SegmentSpec("DivZeroChecker::checkPreStmt", "C.addTransition(stateNotZero);", "C.addTransition(stateNotZero);")], callbacks=["DivZeroChecker::checkPreStmt"], frontends=div_ids, depends=["zero-constraints"], api_names=["clang::ento::CheckerContext::addTransition"], effects=behavior(transitions=["add stateNotZero transition"])),
        ],
    }

    stream_file = f"{SOURCE_ROOT}/SimpleStreamChecker.cpp"
    stream_frontends = [frontend("SimpleStreamChecker", "SimpleStream", "ento::registerSimpleStreamChecker", None)]
    sf = [stream_frontends[0]["id"]]
    stream_callbacks = [
        {"event": "check::PostCall", "method": "SimpleStreamChecker::checkPostCall"},
        {"event": "check::PreCall", "method": "SimpleStreamChecker::checkPreCall"},
        {"event": "check::DeadSymbols", "method": "SimpleStreamChecker::checkDeadSymbols"},
        {"event": "check::PointerEscape", "method": "SimpleStreamChecker::checkPointerEscape"},
    ]
    stream = {
        "implementation_class": "SimpleStreamChecker",
        "summary": "Track fopen streams to detect double close and resource leaks.",
        "analysis_mode": "path_sensitive",
        "source_files": [stream_file],
        "callbacks": stream_callbacks,
        "frontends": stream_frontends,
        "state_traits": [{"name": "StreamMap", "kind": "map", "key_type": "SymbolRef", "value_type": "StreamState", "file": stream_file}],
        "units": [
            unit("open-stream", "state_modeling", "Record a successful fopen result as an opened stream.", [SegmentSpec("SimpleStreamChecker::checkPostCall", "if (!OpenFn.matches(Call))", "C.addTransition(State);")], callbacks=["SimpleStreamChecker::checkPostCall"], frontends=sf, api_names=["clang::ento::CallDescription::matches", "clang::ento::CallEvent::getReturnValue", "clang::ento::CheckerContext::getState", "clang::ento::ProgramState::set", "clang::ento::CheckerContext::addTransition"], effects=behavior(preconditions=["call matches fopen", "return value has a symbol"], state_reads=["current ProgramState"], state_writes=["StreamMap[FileDesc] = Opened"], transitions=["opened stream state"])),
            unit("detect-double-close", "detection", "Detect fclose on a stream already marked closed.", [SegmentSpec("SimpleStreamChecker::checkPreCall", "if (!CloseFn.matches(Call))", "return;", occurrence=1), SegmentSpec("SimpleStreamChecker::checkPreCall", "const StreamState *SS", "return;")], callbacks=["SimpleStreamChecker::checkPreCall"], frontends=sf, api_names=["clang::ento::CallDescription::matches", "clang::ento::CallEvent::getArgSVal", "clang::ento::ProgramState::get"], effects=behavior(state_reads=["StreamMap[FileDesc]"], preconditions=["call matches fclose", "stream symbol is tracked as closed"])),
            unit("close-stream", "state_transition", "Update a live stream to the closed state after fclose.", [SegmentSpec("SimpleStreamChecker::checkPreCall", "State = State->set<StreamMap>(FileDesc, StreamState::getClosed());", "C.addTransition(State);")], callbacks=["SimpleStreamChecker::checkPreCall"], frontends=sf, depends=["detect-double-close"], api_names=["clang::ento::ProgramState::set", "clang::ento::CheckerContext::addTransition"], effects=behavior(state_writes=["StreamMap[FileDesc] = Closed"], transitions=["closed stream state"])),
            unit("double-close-report", "reporting", "Emit a sink report for closing an already closed stream.", [SegmentSpec("SimpleStreamChecker::reportDoubleClose", "void SimpleStreamChecker::reportDoubleClose", "C.emitReport(std::move(R));", "helper")], callbacks=["SimpleStreamChecker::checkPreCall"], frontends=sf, depends=["detect-double-close"], api_names=["clang::ento::CheckerContext::generateErrorNode", "clang::ento::CheckerContext::emitReport"], effects=behavior(reports=["Closing a previously closed file stream"])),
            unit("dead-stream-cleanup", "lifecycle_cleanup", "Find dead opened streams, remove dead symbols from state, and report leaks.", [SegmentSpec("SimpleStreamChecker::checkDeadSymbols", "void SimpleStreamChecker::checkDeadSymbols", "reportLeaks(LeakedStreams, C, N);"), SegmentSpec("isLeaked", "static bool isLeaked", "return false;", "helper"), SegmentSpec("SimpleStreamChecker::reportLeaks", "void SimpleStreamChecker::reportLeaks", "}" , "report_helper", 1)], callbacks=["SimpleStreamChecker::checkDeadSymbols"], frontends=sf, api_names=["clang::ento::CheckerContext::getState", "clang::ento::SymbolReaper::isDead", "clang::ento::ProgramState::remove", "clang::ento::CheckerContext::generateNonFatalErrorNode", "clang::ento::CheckerContext::emitReport"], effects=behavior(state_reads=["all StreamMap entries"], state_writes=["remove dead StreamMap entries"], reports=["Opened file is never closed; potential resource leak"])),
            unit("escaped-stream-cleanup", "escape_handling", "Stop tracking stream symbols that may escape to code which can close them.", [SegmentSpec("SimpleStreamChecker::checkPointerEscape", "SimpleStreamChecker::checkPointerEscape", "State = State->remove<StreamMap>(Sym);"), SegmentSpec("SimpleStreamChecker::guaranteedNotToCloseFile", "bool SimpleStreamChecker::guaranteedNotToCloseFile", "return true;", "helper")], callbacks=["SimpleStreamChecker::checkPointerEscape"], frontends=sf, api_names=["clang::ento::ProgramState::remove"], effects=behavior(state_writes=["remove escaped StreamMap entries"], preconditions=["escape is not a known harmless system call"])),
        ],
    }

    malloc_file = f"{SOURCE_ROOT}/MallocChecker.cpp"
    malloc_names = ["Malloc", "NewDelete", "NewDeleteLeaks", "MismatchedDeallocator", "TaintedAlloc"]
    malloc_members = ["MallocChecker", "NewDeleteChecker", "NewDeleteLeaksChecker", "MismatchedDeallocatorChecker", "TaintedAllocChecker"]
    malloc_frontends = [frontend("MallocChecker", name, f"ento::register{member}", member) for name, member in zip(malloc_names, malloc_members)]
    mf = [item["id"] for item in malloc_frontends]
    malloc_callbacks = [
        {"event": event, "method": f"MallocChecker::{method}"}
        for event, method in [
            ("check::DeadSymbols", "checkDeadSymbols"),
            ("check::PointerEscape", "checkPointerEscape"),
            ("check::ConstPointerEscape", "checkConstPointerEscape"),
            ("check::PreStmt<ReturnStmt>", "checkPreStmt"),
            ("check::EndFunction", "checkEndFunction"),
            ("check::PreCall", "checkPreCall"),
            ("check::PostCall", "checkPostCall"),
            ("eval::Call", "evalCall"),
            ("check::NewAllocator", "checkNewAllocator"),
            ("check::PostStmt<BlockExpr>", "checkPostStmt"),
            ("check::PostObjCMessage", "checkPostObjCMessage"),
            ("check::Location", "checkLocation"),
            ("eval::Assume", "evalAssume"),
        ]
    ]
    malloc = {
        "implementation_class": "MallocChecker",
        "summary": "Model dynamic-memory ownership to detect leaks, invalid frees, double frees, use-after-free, and tainted allocation sizes.",
        "analysis_mode": "path_sensitive",
        "source_files": [malloc_file],
        "callbacks": malloc_callbacks,
        "frontends": malloc_frontends,
        "state_traits": [
            {"name": "RegionState", "kind": "map", "key_type": "SymbolRef", "value_type": "RefState", "file": malloc_file},
            {"name": "ReallocSizeZeroSymbols", "kind": "set", "key_type": "SymbolRef", "value_type": None, "file": malloc_file},
            {"name": "ReallocPairs", "kind": "map", "key_type": "SymbolRef", "value_type": "ReallocPair", "file": malloc_file},
            {"name": "FreeReturnValue", "kind": "map", "key_type": "SymbolRef", "value_type": "SymbolRef", "file": malloc_file},
        ],
        "units": [
            unit("dispatch-pre-call", "entry_filter", "Dispatch recognized deallocation and allocation calls to checker-local models.", [SegmentSpec("MallocChecker::checkPreCall", "void MallocChecker::checkPreCall", "}" , occurrence=1)], callbacks=["MallocChecker::checkPreCall"], frontends=mf),
            unit("model-allocation", "state_modeling", "Bind a newly allocated symbol and record its allocation family in RegionState.", [SegmentSpec("MallocChecker::MallocMemAux", "ProgramStateRef MallocChecker::MallocMemAux", "return State;", "helper", 2)], callbacks=["MallocChecker::checkPostCall", "MallocChecker::checkNewAllocator"], frontends=mf[:2] + [mf[4]], api_names=["clang::ento::ProgramState::set"], effects=behavior(state_writes=["RegionState[allocation symbol] = allocated"], transitions=["allocation state"])),
            unit("model-release", "state_transition", "Validate a deallocation and mark the released symbol in RegionState.", [SegmentSpec("MallocChecker::FreeMemAux", "MallocChecker::FreeMemAux(CheckerContext &C, const Expr *ArgExpr", "return State;", "helper")], callbacks=["MallocChecker::checkPreCall"], frontends=[mf[0], mf[1], mf[3]], depends=["dispatch-pre-call"], api_names=["clang::ento::ProgramState::set", "clang::ento::ProgramState::get"], effects=behavior(state_reads=["RegionState[released symbol]"], state_writes=["RegionState[released symbol] = released"])),
            unit("detect-use-after-free", "detection", "Read RegionState on memory access and report use of a released allocation.", [SegmentSpec("MallocChecker::checkLocation", "void MallocChecker::checkLocation", "}" , occurrence=1), SegmentSpec("MallocChecker::HandleUseAfterFree", "void MallocChecker::HandleUseAfterFree", "}" , "report_helper", 1)], callbacks=["MallocChecker::checkLocation"], frontends=[mf[0], mf[1], mf[4]], depends=["model-release"], api_names=["clang::ento::ProgramState::get", "clang::ento::CheckerContext::emitReport"], effects=behavior(state_reads=["RegionState[accessed symbol]"], reports=["Use of memory after it is freed"])),
            unit("dead-symbol-leaks", "lifecycle_cleanup", "Collect allocated dead symbols as leaks and remove dead allocation state.", [SegmentSpec("MallocChecker::checkDeadSymbols", "void MallocChecker::checkDeadSymbols", "C.addTransition(State);", occurrence=1)], callbacks=["MallocChecker::checkDeadSymbols"], frontends=[mf[0], mf[2]], depends=["model-allocation"], api_names=["clang::ento::SymbolReaper::isDead", "clang::ento::ProgramState::remove", "clang::ento::CheckerContext::addTransition"], effects=behavior(state_reads=["RegionState entries"], state_writes=["remove dead allocation state"], reports=["memory leak"])),
            unit("pointer-escape", "escape_handling", "Relinquish or remove allocation ownership when tracked pointers escape.", [SegmentSpec("MallocChecker::checkPointerEscape", "MallocChecker::checkPointerEscape", "return State;", occurrence=1)], callbacks=["MallocChecker::checkPointerEscape"], frontends=mf, depends=["model-allocation"], api_names=["clang::ento::ProgramState::remove"], effects=behavior(state_writes=["remove or relinquish escaped RegionState entries"])),
        ],
    }
    return [div, stream, malloc]


class DatasetBuilder:
    def __init__(self, llvm_root: Path, api_path: Path):
        self.llvm_root = llvm_root.resolve()
        self.sources = SourceIndex(self.llvm_root)
        self.apis = ApiIndex(api_path)

    def build_checker(self, spec: dict[str, Any]) -> dict[str, Any]:
        checker_name = spec["implementation_class"]
        checker_id = stable_id("checker", checker_name)
        slug_to_id = {
            item["slug"]: stable_id("metaop", f"{checker_name}:{item['slug']}")
            for item in spec["units"]
        }
        logic_units = []
        for order, plan in enumerate(spec["units"], start=1):
            spans, parts = [], []
            for segment in plan["segments"]:
                span, code = self.sources.span(spec["source_files"][0], segment)
                spans.append(span)
                parts.append(code)
            frontend_ids = plan["frontends"]
            if frontend_ids is None:
                frontend_ids = [item["id"] for item in spec["frontends"]]
            logic_units.append(
                {
                    "id": slug_to_id[plan["slug"]],
                    "order": order,
                    "kind": plan["kind"],
                    "meta_op": plan["meta_op"],
                    "callback_context": plan["callback_context"],
                    "applies_to_frontends": frontend_ids,
                    "depends_on": [slug_to_id[slug] for slug in plan["depends"]],
                    "behavior": plan["behavior"],
                    "api_refs": self.apis.refs(plan["api_names"]),
                    "meta_impl": "\n\n".join(parts),
                    "source_spans": spans,
                }
            )
        return {
            "id": checker_id,
            "implementation_class": checker_name,
            "summary": spec["summary"],
            "analysis_mode": spec["analysis_mode"],
            "source_files": spec["source_files"],
            "callbacks": spec["callbacks"],
            "frontends": spec["frontends"],
            "state_traits": spec["state_traits"],
            "logic_units": logic_units,
        }

    def build(self, names: set[str] | None = None) -> dict[str, Any]:
        specs = representative_specs()
        if names:
            unknown = names - {spec["implementation_class"] for spec in specs}
            if unknown:
                raise ValueError(f"no reviewed semantic plan for: {', '.join(sorted(unknown))}")
            specs = [spec for spec in specs if spec["implementation_class"] in names]
        checkers = [self.build_checker(spec) for spec in specs]
        result = self._dataset(checkers)
        validate_dataset(result, self.sources, self.apis.ids)
        return result

    def build_semantic_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        if plan.get("schema_version") != "llm-semantic-plan-1.0":
            raise ValueError("unsupported LLM semantic plan schema")
        checkers = [self._build_semantic_checker(item) for item in plan.get("checkers", [])]
        result = self._dataset(checkers)
        validate_dataset(result, self.sources, self.apis.ids)
        return result

    def _build_semantic_checker(self, plan: dict[str, Any]) -> dict[str, Any]:
        checker_name = plan["implementation_class"]
        raw_frontends = plan.get("frontends", [])
        frontends = []
        seen_frontends = set()
        for item in raw_frontends:
            identity = (item.get("name"), item.get("registration_function"))
            if identity in seen_frontends:
                continue
            seen_frontends.add(identity)
            frontends.append(frontend(
                checker_name,
                item["name"],
                item["registration_function"],
                item.get("frontend_member"),
            ))
        frontend_by_name = {item["name"]: item["id"] for item in frontends}
        raw_units = plan.get("logic_units", [])
        slug_to_id = {
            item["slug"]: stable_id("metaop", f"{checker_name}:{item['slug']}")
            for item in raw_units
        }
        units = []
        for order, item in enumerate(raw_units, start=1):
            spans, source_parts = [], []
            for selector in item["source_selectors"]:
                span = {
                    "role": selector["role"],
                    "symbol": selector["symbol"],
                    "file": selector.get("file", plan["source_files"][0]),
                    "start_line": selector["start_line"],
                    "end_line": selector["end_line"],
                }
                spans.append(span)
                source_parts.append(self.sources.exact_text(span))
            unknown_frontends = set(item["applies_to_frontends"]) - set(frontend_by_name)
            if unknown_frontends:
                raise ValueError(f"{checker_name}/{item['slug']}: unknown frontend names {sorted(unknown_frontends)}")
            unknown_dependencies = set(item["depends_on"]) - set(slug_to_id)
            if unknown_dependencies:
                raise ValueError(f"{checker_name}/{item['slug']}: unknown dependency slugs {sorted(unknown_dependencies)}")
            api_refs = self.apis.refs(item.get("api_names", []), strict=True)
            selected_source = "\n".join(source_parts)
            for api_name in item.get("api_names", []):
                short_name = api_name.rsplit("::", 1)[-1]
                if not re.search(rf"\b{re.escape(short_name)}\s*\(", selected_source):
                    raise ValueError(f"{checker_name}/{item['slug']}: API {api_name} is not called in selected source")
            units.append({
                "id": slug_to_id[item["slug"]],
                "order": order,
                "kind": item["kind"],
                "meta_op": item["meta_op"],
                "callback_context": item["callback_context"],
                "applies_to_frontends": [frontend_by_name[name] for name in item["applies_to_frontends"]],
                "depends_on": [slug_to_id[slug] for slug in item["depends_on"]],
                "behavior": item["behavior"],
                "api_refs": api_refs,
                "meta_impl": "\n\n".join(source_parts),
                "source_spans": spans,
            })
        return {
            "id": stable_id("checker", checker_name),
            "implementation_class": checker_name,
            "summary": plan["summary"],
            "analysis_mode": plan["analysis_mode"],
            "source_files": plan["source_files"],
            "callbacks": plan["callbacks"],
            "frontends": frontends,
            "state_traits": plan.get("state_traits", []),
            "logic_units": units,
        }

    def _dataset(self, checkers: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "metadata": {
                "schema_version": "1.0",
                "dataset": "csa_checker_metaop",
                "llvm_revision": git_revision(self.llvm_root),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_roots": [SOURCE_ROOT],
                "language": ["c", "cpp"],
                "checker_count": len(checkers),
                "logic_unit_count": sum(len(item["logic_units"]) for item in checkers),
            },
            "checkers": checkers,
        }


def validate_dataset(data: dict[str, Any], sources: SourceIndex, api_ids: set[str]) -> None:
    errors: list[str] = []
    metadata = data.get("metadata", {})
    checkers = data.get("checkers", [])
    if metadata.get("schema_version") != "1.0" or metadata.get("dataset") != "csa_checker_metaop":
        errors.append("invalid metadata schema_version or dataset")
    if metadata.get("checker_count") != len(checkers):
        errors.append("metadata.checker_count is stale")
    all_ids: set[str] = set()
    total_units = 0
    for checker in checkers:
        checker_label = checker.get("implementation_class", "<unknown>")
        callback_methods = {item.get("method") for item in checker.get("callbacks", [])}
        frontend_ids = {item.get("id") for item in checker.get("frontends", [])}
        units = checker.get("logic_units", [])
        total_units += len(units)
        unit_ids = {item.get("id") for item in units}
        for record_id in [checker.get("id"), *frontend_ids, *unit_ids]:
            if not isinstance(record_id, str) or ":" not in record_id:
                errors.append(f"{checker_label}: malformed ID {record_id!r}")
            elif record_id in all_ids:
                errors.append(f"duplicate ID: {record_id}")
            else:
                all_ids.add(record_id)
        if [unit.get("order") for unit in units] != list(range(1, len(units) + 1)):
            errors.append(f"{checker_label}: logic unit order is not contiguous")
        graph: dict[str, list[str]] = {}
        for logic in units:
            label = logic.get("id", "<unknown>")
            if logic.get("kind") not in KINDS:
                errors.append(f"{label}: invalid kind {logic.get('kind')!r}")
            if set(logic.get("behavior", {})) != set(BEHAVIOR_FIELDS):
                errors.append(f"{label}: behavior must contain exactly {BEHAVIOR_FIELDS}")
            bad_callbacks = set(logic.get("callback_context", [])) - callback_methods
            if bad_callbacks:
                errors.append(f"{label}: unknown callbacks {sorted(bad_callbacks)}")
            bad_frontends = set(logic.get("applies_to_frontends", [])) - frontend_ids
            if bad_frontends:
                errors.append(f"{label}: unknown frontends {sorted(bad_frontends)}")
            dependencies = logic.get("depends_on", [])
            graph[label] = dependencies
            missing = set(dependencies) - unit_ids
            if missing:
                errors.append(f"{label}: missing dependencies {sorted(missing)}")
            unresolved = [ref.get("id") for ref in logic.get("api_refs", []) if ref.get("id") not in api_ids]
            if unresolved:
                errors.append(f"{label}: API IDs absent from Stage 1: {unresolved}")
            try:
                for span in logic.get("source_spans", []):
                    if span.get("file") not in checker.get("source_files", []):
                        errors.append(f"{label}: source span file is not owned by checker")
                    if span.get("start_line", 0) > span.get("end_line", -1):
                        errors.append(f"{label}: reversed source span")
                rebuilt = "\n\n".join(sources.exact_text(span) for span in logic.get("source_spans", []))
                if rebuilt != logic.get("meta_impl"):
                    errors.append(f"{label}: meta_impl differs from source spans")
            except (KeyError, OSError, IndexError) as exc:
                errors.append(f"{label}: invalid source span: {exc}")
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(node: str) -> None:
            if node in visiting:
                errors.append(f"{checker_label}: dependency cycle at {node}")
                return
            if node in visited:
                return
            visiting.add(node)
            for dependency in graph.get(node, []):
                visit(dependency)
            visiting.remove(node)
            visited.add(node)
        for node in graph:
            visit(node)
    if metadata.get("logic_unit_count") != total_units:
        errors.append("metadata.logic_unit_count is stale")
    if errors:
        raise ValueError("invalid CSA meta-op dataset:\n- " + "\n- ".join(errors))


def merge_datasets(base: dict[str, Any], updates: dict[str, Any], sources: SourceIndex, api_ids: set[str]) -> dict[str, Any]:
    """Replace updated implementation classes while retaining other checkers."""
    by_class = {item["implementation_class"]: item for item in base.get("checkers", [])}
    by_class.update({item["implementation_class"]: item for item in updates.get("checkers", [])})
    checkers = [by_class[name] for name in sorted(by_class)]
    merged = {
        "metadata": {
            **base.get("metadata", {}),
            "schema_version": "1.0",
            "dataset": "csa_checker_metaop",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "checker_count": len(checkers),
            "logic_unit_count": sum(len(item["logic_units"]) for item in checkers),
        },
        "checkers": checkers,
    }
    validate_dataset(merged, sources, api_ids)
    return merged


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm-root", type=Path, default=Path("/home/llvm/llvm-project"))
    parser.add_argument("--api-json", type=Path, default=here.parent / "csa_official_api_extract/csa_api.json")
    parser.add_argument("--output", type=Path, default=here / "csa_meat_op.json")
    parser.add_argument("--checker", action="append", dest="checkers", help="Build one reviewed implementation class (repeatable)")
    parser.add_argument("--validate", type=Path, help="Validate an existing canonical dataset instead of building")
    parser.add_argument("--inventory-output", type=Path, help="Write a transient Tree-sitter callback/helper inventory")
    parser.add_argument("--semantic-plan", type=Path, help="Build canonical JSON from validated LLM semantic-plan JSON")
    parser.add_argument("--merge-into", type=Path, help="Merge semantic-plan checkers into an existing Stage 2 dataset")
    parser.add_argument("--compact", action="store_true", help="Write compact JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    builder = DatasetBuilder(args.llvm_root, args.api_json)
    if args.inventory_output:
        inventory = scan_checker_sources(args.llvm_root, set(args.checkers) if args.checkers else None)
        args.inventory_output.parent.mkdir(parents=True, exist_ok=True)
        args.inventory_output.write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Saved static inventory for {len(inventory['files'])} source files to {args.inventory_output}")
    if args.validate:
        data = json.loads(args.validate.read_text(encoding="utf-8"))
        validate_dataset(data, builder.sources, builder.apis.ids)
        print(f"Validated {args.validate}")
        return 0
    if args.semantic_plan:
        plan = json.loads(args.semantic_plan.read_text(encoding="utf-8"))
        data = builder.build_semantic_plan(plan)
        if args.merge_into:
            existing = json.loads(args.merge_into.read_text(encoding="utf-8"))
            data = merge_datasets(existing, data, builder.sources, builder.apis.ids)
    else:
        data = builder.build(set(args.checkers) if args.checkers else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=None if args.compact else 2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved {data['metadata']['checker_count']} checkers and {data['metadata']['logic_unit_count']} logic units to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
