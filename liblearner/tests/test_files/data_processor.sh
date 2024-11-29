#!/bin/bash

# Data Processing Script
# Handles CSV and JSON data transformations with various formatting options

# Configuration variables
INPUT_DIR="./data/input"
OUTPUT_DIR="./data/output"
TEMP_DIR="./data/temp"
CSV_DELIMITER=","
JSON_INDENT=2

# Import helper functions
source ./lib/csv_helpers.sh
source ./lib/json_helpers.sh

# Set useful aliases for data operations
alias csvhead='head -n1'
alias jsontool='python -m json.tool'
alias countlines='wc -l'

# Convert CSV to JSON
# Args: input_file output_file
convert_csv_to_json() {
    local input="$1"
    local output="$2"
    
    # Read header line
    local header=($(head -n1 "$input" | tr "$CSV_DELIMITER" ' '))
    
    # Process data lines
    echo "[" > "$output"
    local first_line=true
    
    while IFS="$CSV_DELIMITER" read -r -a values; do
        # Skip header
        [[ "$first_line" == true ]] && { first_line=false; continue; }
        
        # Create JSON object
        local json="{"
        for i in "${!header[@]}"; do
            [[ $i -gt 0 ]] && json+=","
            json+="\"${header[$i]}\":\"${values[$i]}\""
        done
        json+="}"
        
        # Append to output
        echo "  $json," >> "$output"
    done < "$input"
    
    # Clean up and close JSON array
    sed -i '$ s/,$//' "$output"
    echo "]" >> "$output"
}

# Process JSON data
process_json() {
    local input=$1
    local output=$2
    local filter=$3
    
    # Apply jq filter if provided
    if [[ -n "$filter" ]]; then
        cat "$input" | jq "$filter" > "$output"
    else
        cat "$input" | jq '.' > "$output"
    fi
}

# Validate CSV format
validate_csv() {
    local file="$1"
    local expected_cols
    
    # Get number of columns from header
    expected_cols=$(head -n1 "$file" | tr -cd "$CSV_DELIMITER" | wc -c)
    expected_cols=$((expected_cols + 1))
    
    # Check each line
    local line_num=0
    local errors=0
    
    while IFS= read -r line; do
        ((line_num++))
        local cols=$(echo "$line" | tr -cd "$CSV_DELIMITER" | wc -c)
        cols=$((cols + 1))
        
        if [[ $cols -ne $expected_cols ]]; then
            echo "Error on line $line_num: Expected $expected_cols columns, found $cols"
            ((errors++))
        fi
    done < "$file"
    
    return $errors
}

# Clean and normalize CSV data
clean_csv() {
    local input="$1"
    local output="$2"
    
    # Remove empty lines and normalize delimiters
    sed '/^[[:space:]]*$/d' "$input" | \
        sed 's/[[:space:]]*'"$CSV_DELIMITER"'[[:space:]]*/'"$CSV_DELIMITER"'/g' > "$output"
}

# Initialize directories
init_dirs() {
    for dir in "$INPUT_DIR" "$OUTPUT_DIR" "$TEMP_DIR"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            echo "Created directory: $dir"
        fi
    done
}

# Main processing function
main() {
    local input_file="$1"
    local output_file="$2"
    local format="${3:-json}"
    
    # Initialize
    init_dirs
    
    case "$format" in
        "json")
            if [[ "$input_file" =~ \.csv$ ]]; then
                convert_csv_to_json "$input_file" "$output_file"
            else
                process_json "$input_file" "$output_file"
            fi
            ;;
        "csv")
            clean_csv "$input_file" "$output_file"
            validate_csv "$output_file"
            ;;
        *)
            echo "Unsupported format: $format"
            return 1
            ;;
    esac
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 2 ]]; then
        echo "Usage: $0 input_file output_file [format]"
        exit 1
    fi
    
    main "$@"
fi
