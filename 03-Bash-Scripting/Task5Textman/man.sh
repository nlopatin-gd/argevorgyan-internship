#!/bin/bash

while getopts "i:o:s:vrlu" opt; do #getting options
  case "$opt" in
    i) input_file=$OPTARG ;;
    o) output_file=$OPTARG ;;
    s) sub_arg=$OPTARG ;; #replace
    v) flip=true ;;
    r) reverse=true ;;
    l) lower=true ;;
    u) upper=true ;;
    *) echo "Usage: $0 -i <input> -o <output> [-v] [-s 'A B'] [-r] [-l] [-u']"; exit 1 ;; #if usage is wrong
  esac
done

[[ -z $input_file || -z $output_file ]] && { echo "Missing input/output file"; exit 1;} #val input of files

[[ ! -f $input_file ]] && { echo "Input file not found: $input_file"; exit 1;}  #val file existence

# Start from input file
input_str="cat \"$input_file\""

if [[ $sub_arg ]]; then
  a=$(echo "$sub_arg" | awk '{print $1}') #get first word
  b=$(echo "$sub_arg" | awk '{print $2}') #get second word
  if ! grep -q $a $input_file; then
  echo "Error: The string '$a' is not present in '$input_file'."
fi
  input_str+=" | sed 's/$a/$b/g'"
fi

# apply transformations
[[ $flip ]] && input_str+=" | tr 'A-Za-z' 'a-zA-Z'" # flip uppercase and lowercase
[[ $lower ]] && input_str+=" | tr 'A-Z' 'a-z'" # convert to lowercase
[[ $upper ]] && input_str+=" | tr 'a-z' 'A-Z'" # Convert to uppercase

# Reverse line order
[[ $reverse ]] && input_str+=" | tac"

eval "$input_str" > "$output_file"