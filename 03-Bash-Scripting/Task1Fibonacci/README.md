
# 🧮 Fibonacci Bash Script
This script asks the user to enter a number and then shows the Fibonacci number at that position.

---

## How I Wrote the Script

- First, I used `echo` to show a welcome message so the user knows what the script does.
- Then I set default values:

```bash
f0=0  # first Fibonacci number
f1=1  # second Fibonacci number
```

- I wrote simple conditions:
  - If the input number is `0`, it just prints `f0`
  - If the input is `1`, it prints `f1`

- If the number is more than `1`, I use a loop starting from `2`, because the first two values we  already set up

- Inside the loop:
  - It adds the two previous numbers to get the next one:
  
  ```bash
  sum=$((f0 + f1))
  ```

  - Then updates the previous numbers:

  ```bash
  f0=$f1
  f1=$sum
  ```
  - I came up with the looping solution by noticing how Fibonacci numbers grow: each number depends on the sum of the previous two numbers.  
  Since the two previous numbers change as we move forward, it feels like a simple step-by-step progression.  for example 3 is 1+2, 5 is 2+3 etc

- This keeps going until we reach the number the user entered.

---

## Bash Limit for Big Numbers

While testing, I discovered that Bash can't handle Fibonacci numbers above position `92` correctly — the numbers become too big.

added a check:

```bash
if (( n > 92 )); then
    echo "Max allowed is 92 because of Bash integer limits"
    exit 1  # exit with error
fi
```
---

## Example

```bash
=======================
Fibonacci Numbers Task
=======================
Enter number to find the fibonacci number! c:
10
Your number: 10 as fibonacci number is: 55
=======================
```

---

