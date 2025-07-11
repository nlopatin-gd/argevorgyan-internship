# Mini calculator script

## Task
script that performs basic arithmetic operations on a list of numbers passed as command-line arguments.

The script must:
- Accept an operation flag `-o` followed by an operator (`+`, `-`, `*`, `%`)
- Accept a list of numbers using `-n`
- Optionally accept a debug flag `-d` to print execution details

## Example 

```bash
./calculator.sh -o + -n 2 4 6 -d
```

output
```
User: areg
Script: ./minicalc.sh
Operation: +
Numbers: 2 4 6
Result: 12
```
---