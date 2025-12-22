#!/bin/bash

# Check for correct arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <directory_path> <label>"
    echo "Example: $0 ./cat_images cat"
    exit 1
fi

DIRECTORY="$1"
LABEL="$2"
ENDPOINT="http://localhost:42069/admin/fer/data/upload" # Change port/host if needed
MANIFEST="manifest.csv"

# 1. Create the CSV header
echo "filename,label" > "$MANIFEST"

# Initialize array for curl command
# We use an array to handle potential spaces in filenames safely
CURL_ARGS=(-X POST "$ENDPOINT")

echo "Preparing upload for directory: $DIRECTORY"

COUNT=0

# 2. Loop through files
for filepath in "$DIRECTORY"/*; do
    # Check if it is a regular file
    if [ -f "$filepath" ]; then
        filename=$(basename "$filepath")

        # Add row to manifest CSV
        echo "$filename,$LABEL" >> "$MANIFEST"

        # Add file argument to curl command
        # "files" matches the FastAPI argument: files: List[UploadFile]
        CURL_ARGS+=(-F "files=@$filepath")

        ((COUNT++))

        if [ "$COUNT" -ge 999 ]; then
            break
        fi
    fi
done

if [ "$COUNT" -eq 0 ]; then
    echo "No files found in $DIRECTORY."
    rm "$MANIFEST"
    exit 1
fi

# 3. Add the manifest file to the request
CURL_ARGS+=(-F "manifest_file=@$MANIFEST")

# 4. Execute curl
echo "Uploading $COUNT files..."
curl "${CURL_ARGS[@]}"

# Cleanup
rm "$MANIFEST"
echo -e "\nDone."
