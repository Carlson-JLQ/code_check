Extract a JSON list of detection logic units for a Clang Static Analyzer checker.
Rule: Prohibit omitting the else branch of if-else if statements. In all if-else if statement structures, the final else branch must be included, even if it does not perform any operations, and must be explicitly written. This is to ensure the logical integrity of the code and prevent undefined behavior due to omitted conditions. This rule applies to any conditional statement chain that contains one or more else if branches; the final else branch must exist to handle all uncovered condition scenarios. If the else branch is empty, it should include appropriate comments (e.g.,  Other cases not handled ). Compliant scenarios include if-else if statements that contain an else branch (whether empty or not), while non-compliant scenarios involve omitting the final else branch. The rule checks the structural integrity of conditional statements, not whether the else branch contains specific logic.
Negative test:
#include <stdio.h>

int calculate_level(int value) {
    int level;
    if (value > 100) {
        level = 3;
    } else if (value > 50) {
        level = 2;
    } else if (value > 10) {
        level = 1;
    }
    level = 0;  // 违反：赋值语句代替else分支
    // CHECK-MESSAGES: 禁止省略 if-else if 语句的 else 分支 [gjb8114-r-1-4-1]
    return level;
}

int main(void) {
    printf("%d\n", calculate_level(75));
    return 0;
}
Each unit must contain intent, trigger, constraints, and CSA API search terms.
Return JSON only.
