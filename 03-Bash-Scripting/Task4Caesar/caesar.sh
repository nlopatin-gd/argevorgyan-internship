#!/bin/bash

while getopts "s:i:o:" opt; do
  case "$opt" in
    s) shift_amt=$OPTARG ;; #shift amount
    i) input_file=$OPTARG ;; # inp file 
    o) output_file=$OPTARG ;; # outp file
    *) echo "Usage: $0 -s <shift> -i <input> -o <output>"; exit 1 ;; #input validation
  esac
done

#input validation
if ! [[ "$shift_amt" =~ ^-?[0-9]+$ ]]; then
  echo "Error: Shift amount must be an integer"
  exit 1
fi

[[ -z $shift_amt || -z $input_file || -z $output_file ]] && {
  echo "Missing required arguments"; exit 1;
}

[[ ! -f $input_file ]] && {                               #if there was no input file found exit with 1
  echo "Input file not found: $input_file"; exit 1; 
}
#function using tr with dynamically shifted alphabets
caesar() { 
 upper=ABCDEFGHIJKLMNOPQRSTUVWXYZ
 lower=abcdefghijklmnopqrstuvwxyz
 shift=$((shift_amt % 26))
 shifted_upper="${upper:shift}${upper:0:shift}"
 shifted_lower="${lower:shift}${lower:0:shift}"
  tr 'A-Za-z' "$shifted_upper$shifted_lower"
}
caesar < "$input_file" > "$output_file"