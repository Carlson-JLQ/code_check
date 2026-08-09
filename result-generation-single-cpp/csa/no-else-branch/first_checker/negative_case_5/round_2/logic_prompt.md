Extract a JSON list of detection logic units for a Clang Static Analyzer checker.
Rule: Prohibit omitting the else branch of if-else if statements. In all if-else if statement structures, the final else branch must be included, even if it does not perform any operations, and must be explicitly written. This is to ensure the logical integrity of the code and prevent undefined behavior due to omitted conditions. This rule applies to any conditional statement chain that contains one or more else if branches; the final else branch must exist to handle all uncovered condition scenarios. If the else branch is empty, it should include appropriate comments (e.g.,  Other cases not handled ). Compliant scenarios include if-else if statements that contain an else branch (whether empty or not), while non-compliant scenarios involve omitting the final else branch. The rule checks the structural integrity of conditional statements, not whether the else branch contains specific logic.
Negative test:
#include <stdio.h>

int nested_check(int a, int b) {
    if (a > 0) {
        if (b > 0) {
            return 1;
        } else if (b < 0) {
            return 2;
        }
        return 3;  // 内层省略else，但这是单独的if-else if结构
    } else if (a < 0) {
        return 4;
    }
    return 5;  // 违反：外层if-else if省略else
    // CHECK-MESSAGES: 禁止省略 if-else if 语句的 else 分支 [gjb8114-r-1-4-1]
}

int main(void) {
    printf("%d\n", nested_check(1, 1));
    return 0;
}
Each unit must contain intent, trigger, constraints, and CSA API search terms.
Return JSON only.
