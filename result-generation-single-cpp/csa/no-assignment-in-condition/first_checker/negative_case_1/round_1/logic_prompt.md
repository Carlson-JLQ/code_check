Extract a JSON list of detection logic units for a Clang Static Analyzer checker.
Rule: Prohibited is the direct use of assignment statements in logical expressions (such as conditional statements like if, while, for), aimed at preventing logical errors caused by mistakenly using the assignment operator (=) instead of the comparison operator (==). When an assignment statement is used in a logical expression, the assignment operation itself returns a value, which is implicitly converted to a boolean value for conditional evaluation. This may cause the conditional evaluation to deviate from the expected logic (such as non-zero values being converted to true, and zero values to false), potentially leading to hard-to-detect program errors. This rule requires that assignment operations must be separated from conditional evaluations, meaning that assignment should be performed first, followed by conditional evaluation using a comparison operator. Compliant scenarios include using only comparison operators (such as ==, !=) in conditions, assigning first and then comparing, or using boolean variables to store the result; non-compliant scenarios involve directly using the assignment operator in conditions (such as if (x = y)), regardless of whether the assignment is combined with a comparison operation.
Negative test:
#include <stdio.h>

int main(void) {
    int a = 0, b = 5;
    if (a = b) {  // 违反：在if条件中使用赋值语句
        // CHECK-MESSAGES: 禁止将赋值语句作为逻辑表达式 [gjb8114-r-1-6-3]
        printf("a is now %d\n", a);
    }
    return 0;
}
Each unit must contain intent, trigger, constraints, and CSA API search terms.
Return JSON only.
