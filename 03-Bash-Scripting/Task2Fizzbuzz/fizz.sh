#!/bin/bash
#fizzbuzz task, prints numbers from 1 to 100 if its multiple of 3 prints "Fizz",
#if its multiple of 5 prints "Buzz", if its multiple of both prints "FizzBuzz"
echo "multiples of 3 and 5 from 1 to 100"
for ((i=1; i<=100; i++)); do
  if (( i % 3 == 0 && i % 5 == 0 )); then
    echo "FizzBuzz"
  elif (( i % 3 == 0 )); then
    echo "Fizz"
  elif (( i % 5 == 0 )); then
    echo "Buzz"
  else
    echo "$i"
  fi
done
