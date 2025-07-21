#!/bin/bash
#fibonacci numbers task
clear
echo "======================="
echo "Fibonacci Numbers Task"
echo "======================="
f0=0                            #set first two known fibonacci numbers
f1=1 

fib(){
	if [ $n -eq 0 ]; then       #first two cases in which we are sure of
		echo $f0
	elif [ $n -eq 1 ]; then  
		echo $f1
	else
		for (( i=2; i<=n; i++ )); do  #loop from 2 to  our users input number to get its position
			sum=$((f0 + f1)) #getting next number by adding prev two
			f0=$f1
			f1=$sum
		done
		echo $f1 #output last number which is the fibo of our input 
	fi
}
echo "Enter number to find the fibonacci number! c:"
echo "=================================================="
read n
    if [ $n -gt 92 ]; then #check if input goes beyond bash limits
    echo "max allowed is 92 because of  Bash integer limits"
    exit 1; elif [ $n -lt 0 ]; then #check if input is negative
	echo "Negative numbers are not allowed"
	exit 1; elif [ -z "$n" ]; then #check if input is empty
	echo "Input cannot be empty"
	exit 1; elif ! [[ "$n" =~ ^[0-9]+$ ]]; then #check if input is not a number
	echo "Input must be a positive integer"
	exit 1; fi
echo "Your number: $n as fibonacci number is: $(fib $n)"
echo "=================================================="
exit 0