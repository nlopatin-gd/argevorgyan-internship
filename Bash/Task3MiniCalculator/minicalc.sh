#!/bin/bash
# simple one line calculator
if [[ "$1" == "-o" ]]; then #first arg
  op="$2" #store arg to var
  case "$op" in
    "+"|"-"|"*"|"%" ) ;;  # op input validation
    * )
      echo "Error: Invalid operator '$op'. Use +, -, *, or %."
      exit 1
      ;;
  esac
fi

shift 2 

if [[ "$1" == "-n" ]]; then #check if next arg is n
  shift
  nums=() #array for numbers
  while [[ "$1" != "-d" && "$1" != "" ]]; do #every arg will be number till d flag or empty
    nums+=("$1")
    shift
  done
fi

if [[ "$1" == "-d" ]]; then #if -d flag is passed set debug to true
  debug=true
fi

res="${nums[0]}" # start from first number
for ((i = 1; i < ${#nums[@]}; i++)); do #moving through num array
  case "$op" in #check op
    +) res=$((res + nums[i])) ;;
    -) res=$((res - nums[i])) ;;
    \*) res=$((res * nums[i])) ;;
    %) res=$((res % nums[i])) ;;
  esac
done

# Debug
if [[ "$debug" == true ]]; then
  echo "User: $(whoami)"
  echo "Script: $0"
  echo "Operation: $op"
  echo "Numbers: ${nums[*]}"
fi

echo "Result: $res"