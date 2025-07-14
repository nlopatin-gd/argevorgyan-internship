#!/bin/bash
op="" 
nums=() # array for numbers

#  options with getopts
while getopts ":o:n:d" opt; do
  case "$opt" in
    o)
      op="$OPTARG"
      case "$op" in
        "+"|"-"|"*"|"%") ;;
        *)
          echo "Use +, -, *, or %."
          exit 1
          ;;
      esac
      ;;
    d)
      debug=true
      ;;
    n)
      # getopts only takes one value, so collect rest manually after -n
      shift $((OPTIND - 2)) # shift to the first number
      #add numbers til next flag or end of args
      while [[ "$1" =~ ^-?[0-9]+$ ]]; do
        nums+=("$1")
        shift #move to next arg
      done
      break
      ;;
    \?)
      echo "Usage: $0 -o [+|-|*|%] [-d] -n num1 num2 "
      exit 1
      ;;
  esac
done

if [[ -z "$op" ]]; then # val if operator is set     
  echo "Operator not specified. Use -o [+|-|*|%]"
  exit 1
fi

if [[ "${#nums[@]}" -lt 2 ]]; then #validate that at least two numbers are included
  echo "At least two numbers are required after -n"
  exit 1
fi

# result calculation
res="${nums[0]}"
for ((i = 1; i < ${#nums[@]}; i++)); do
  case "$op" in
    +) res=$((res + nums[i])) ;;
    -) res=$((res - nums[i])) ;;
    \*) res=$((res * nums[i])) ;;
    %)
      if [[ "${nums[i]}" -eq 0 ]]; then # check for division by zero
        echo "Error: Division by zero"
        exit 1
      fi
      res=$((res % nums[i])) ;;
  esac
done

if [[ "$debug" == true ]]; then
  echo "User: $(whoami)"
  echo "Script: $0"
  echo "Operation: $op"
  echo "Numbers: ${nums[*]}"
fi

echo "Result: $res"