"""Domain objects for Clang Static Analyzer checker generation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from entity.abstractProduct import AbstractCase, AbstractChecker, AbstractRule


@dataclass(eq=False)
class Case_CSA(AbstractCase):
    case_code: str = ""
    case_description: str = ""
    case_flag: bool = False  # CodeQL-compatible convention: True means positive.
    case_path: str = ""
    skipped: bool = False
    expected_diagnostics: List[str] = field(default_factory=list)
    last_result: Optional[Dict[str, Any]] = None

    def getInfo(self):
        return "This is a CSA case"

    def get_case_id(self):
        return self.case_path

    def get_case_description(self):
        return self.case_description

    def get_case_code(self):
        return self.case_code

    def get_case_path(self):
        return self.case_path

    def get_flag(self):
        return self.case_flag

    def __str__(self):
        return f"Case_CSA(path={self.case_path!r}, positive={self.case_flag})"


@dataclass
class Checker_CSA(AbstractChecker):
    checker_code: str = ""
    header_code: str = ""
    passed_cases: List[Case_CSA] = field(default_factory=list)
    name: str = "GeneratedNoAssignmentInConditionChecker"
    frontend: str = "gjb8114.NoAssignmentInCondition"
    plugin_path: str = ""
    version: int = 1
    generation_kind: str = "initial"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def getInfo(self):
        return "This is a CSA checker"

    def get_checker_code(self):
        return self.checker_code

    def get_passed_cases(self):
        return self.passed_cases

    def add_passed_cases(self, case):
        if case not in self.passed_cases:
            self.passed_cases.append(case)
        return True

    def set_passed_cases(self, cases):
        self.passed_cases = list(cases)

    def set_checker_code(self, code):
        self.checker_code = code
        return True

    def clear_passed_cases(self):
        self.passed_cases = []
        return True

    def snapshot(self):
        return {
            "name": self.name,
            "frontend": self.frontend,
            "plugin_path": self.plugin_path,
            "version": self.version,
            "generation_kind": self.generation_kind,
            "passed_case_amount": len(self.passed_cases),
            "passed_cases": [str(case.get_case_path()) for case in self.passed_cases],
            "metadata": self.metadata,
        }


class Rule_CSA(AbstractRule):
    def __init__(
        self,
        rule_name="no-assignment-in-condition",
        rule_description=(
            "Assignment operations must not be used directly in logical "
            "conditions such as if, while, do-while, or for conditions."
        ),
        rule_test_path="",
        rule_category="gjb8114",
        rule_id="gjb8114-r-1-6-3",
        diagnostic="禁止将赋值语句作为逻辑表达式",
    ):
        self.rule_name = rule_name
        self.rule_description = rule_description
        self.rule_test_path = rule_test_path
        self.rule_category = rule_category
        self.rule_id = rule_id
        self.diagnostic = diagnostic
        self.checkers: List[Checker_CSA] = []

    def getInfo(self):
        return "This is a CSA rule"

    def get_rule_name(self):
        return self.rule_name

    def get_rule_description(self):
        return self.rule_description

    def get_rule_test_path(self):
        return self.rule_test_path

    def get_rule_category(self):
        return self.rule_category

    def add_checker(self, checker):
        self.checkers.append(checker)

    def get_checkers(self):
        return self.checkers

    def set_rule_description(self, value):
        self.rule_description = value

    def get_rule_id(self):
        return self.rule_id

    def get_diagnostic(self):
        return self.diagnostic

    @classmethod
    def from_rule_record(cls, record, test_path="", rule_id=None, diagnostic=None):
        return cls(
            rule_name=record.get("main_title", "no-assignment-in-condition"),
            rule_description=record.get("description", ""),
            rule_test_path=str(test_path or record.get("rule_test_path", "")),
            rule_category=record.get("category", "gjb8114"),
            rule_id=rule_id or record.get("rule_id") or "unknown-gjb8114-rule",
            diagnostic=diagnostic or record.get("diagnostic") or "GJB8114 rule violation",
        )
