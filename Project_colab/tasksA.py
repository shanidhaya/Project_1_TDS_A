import os
import re
import json
import shutil
import base64
import sqlite3
import subprocess
import requests
import openai
import pytesseract
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from dateutil.parser import parse
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from scipy.spatial.distance import cosine

load_dotenv()

AIPROXY_TOKEN = os.getenv('AIPROXY_TOKEN')


def A1(email="22f2000813@ds.study.iitm.ac.in"):
    try:
        process = subprocess.Popen(
            ["uv", "run", "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py", email],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error: {stderr}")
        return stdout
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error: {e.stderr}")
# A1()
def A2():
    """
    Formats the file /data/format.md using prettier@3.4.2.
    The file is updated in-place.
    
    This version mimics the evaluation script: it pipes the file content into Prettier
    using the "--stdin-filepath /data/format.md" option.
    """
    # Define the local data directory (project-root/data)
    local_data_dir = os.path.join(os.getcwd(), "data")
    
    # Construct the local file path for format.md
    file_path = os.path.join(local_data_dir, "format.md")
    
    # Check if the file exists
    if not os.path.exists(file_path):
        raise Exception(f"File not found: {file_path}")
    
    # Read the current contents of the file.
    with open(file_path, "r") as f:
        original = f.read()
    
    try:
        # Build the command as a single string.
        cmd = "npx prettier@3.4.2 --stdin-filepath /data/format.md"
        # Run Prettier using the command string, passing the current working directory and environment.
        proc = subprocess.run(
            cmd,
            input=original,
            capture_output=True,
            text=True,
            check=True,
            shell=True,  # Command is provided as a string.
            cwd=os.getcwd(),         # Ensure we run in the project root.
            env=os.environ.copy()      # Pass the current environment.
        )
        formatted = proc.stdout
        
        # Write the formatted content back to the file.
        with open(file_path, "w") as f:
            f.write(formatted)
        
        return {"stdout": formatted, "stderr": proc.stderr}
    except subprocess.CalledProcessError as e:
        raise Exception("Error formatting file: " + e.stderr)


def A3(filename='/data/dates.txt', targetfile='/data/dates-wednesdays.txt', weekday=2):
    input_file = filename
    output_file = targetfile
    weekday = weekday
    weekday_count = 0

    with open(input_file, 'r') as file:
        weekday_count = sum(1 for date in file if parse(date).weekday() == int(weekday)-1)


    with open(output_file, 'w') as file:
        file.write(str(weekday_count))

def A4(filename="/data/contacts.json", targetfile="/data/contacts-sorted.json"):
    # Load the contacts from the JSON file
    with open(filename, 'r') as file:
        contacts = json.load(file)

    # Sort the contacts by last_name and then by first_name
    sorted_contacts = sorted(contacts, key=lambda x: (x['last_name'], x['first_name']))

    # Write the sorted contacts to the new JSON file
    with open(targetfile, 'w') as file:
        json.dump(sorted_contacts, file, indent=4)

def A5(log_dir_path='/data/logs', output_file_path='/data/logs-recent.txt', num_files=10):
    log_dir = Path(log_dir_path)
    output_file = Path(output_file_path)

    # Get list of .log files sorted by modification time (most recent first)
    log_files = sorted(log_dir.glob('*.log'), key=os.path.getmtime, reverse=True)[:num_files]

    # Read first line of each file and write to the output file
    with output_file.open('w') as f_out:
        for log_file in log_files:
            with log_file.open('r') as f_in:
                first_line = f_in.readline().strip()
                f_out.write(f"{first_line}\n")

def A6(doc_dir_path='/data/docs', output_file_path='/data/docs/index.json'):
    docs_dir = doc_dir_path
    output_file = output_file_path
    index_data = {}

    # Walk through all files in the docs directory
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                # print(file)
                file_path = os.path.join(root, file)
                # Read the file and find the first occurrence of an H1
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('# '):
                            # Extract the title text after '# '
                            title = line[2:].strip()
                            # Get the relative path without the prefix
                            relative_path = os.path.relpath(file_path, docs_dir).replace('\\', '/')
                            index_data[relative_path] = title
                            break  # Stop after the first H1
    # Write the index data to index.json
    # print(index_data)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=4)

def A7(filename='/data/email.txt', output_file='/data/email-sender.txt'):
    # Read the content of the email
    with open(filename, 'r') as file:
        email_content = file.readlines()

    sender_email = "sujay@gmail.com"
    for line in email_content:
        if "From" == line[:4]:
            sender_email = (line.strip().split(" ")[-1]).replace("<", "").replace(">", "")
            break

    # Get the extracted email address

    # Write the email address to the output file
    with open(output_file, 'w') as file:
        file.write(sender_email)

import base64
def png_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_string

def passes_luhn(card_number):
    """Returns True if card_number passes Luhn's algorithm."""
    digits = [int(d) for d in card_number]
    checksum = 0
    double = False

    for i in range(len(digits) - 1, -1, -1):
        d = digits[i]
        if double:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
        double = not double

    return checksum % 10 == 0

def A8():
    """
    1. Reads /data/credit_card.png
    2. Extracts a 16-digit number via Tesseract OCR
    3. Applies Luhn check. If it fails, attempts minor OCR correction.
    4. Writes the final 16-digit number to /data/credit-card.txt
    """
    input_file = os.path.join(os.getcwd(), "data", "credit_card.png")
    output_file = os.path.join(os.getcwd(), "data", "credit-card.txt")

    try:
        # 1. Load the image
        img = Image.open(input_file)

        # 2. Configure Tesseract
        custom_config = r"--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789"
        extracted_text = pytesseract.image_to_string(img, config=custom_config)

        # 3. Extract potential numbers
        lines = extracted_text.splitlines()
        recognized_16 = None
        for line in lines:
            digits = re.sub(r"\D", "", line)  # Keep only digits
            if len(digits) == 16:
                recognized_16 = digits
                break

        if not recognized_16:
            return {
                "error": "No valid 16-digit number found.",
                "ocr_output": extracted_text
            }

        # 4. Validate with Luhn
        if passes_luhn(recognized_16):
            final_number = recognized_16
        else:
            # Attempt a minor correction (flipping common OCR mistakes)
            possible_corrections = {
                '8': '3', '3': '8', '0': '6', '6': '0', '5': '9', '9': '5'
            }
            corrected_number = ''.join(
                possible_corrections.get(d, d) for d in recognized_16
            )

            if passes_luhn(corrected_number):
                final_number = corrected_number
            else:
                return {
                    "error": "Luhn check failed after OCR correction.",
                    "recognized_number": recognized_16
                }

        # 5. Write the final number to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_number + "\n")

        return {"written_file": output_file, "card_number": final_number}

    except Exception as e:
        return {"error": str(e)}

def A9():
    """
    Reads /data/comments.txt (one comment per line).
    Asks GPT-4o-Mini to pick the two lines that are most semantically similar.
    Writes those two lines (one per line) to /data/comments-similar.txt.
    """
    # 1. Prepare file paths
    input_file = os.path.join(os.getcwd(), "data", "comments.txt")
    output_file = os.path.join(os.getcwd(), "data", "comments-similar.txt")

    # 2. Check if the file exists
    if not os.path.exists(input_file):
        return {"error": f"{input_file} does not exist"}

    # 3. Read lines (strip empty ones)
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        return {"error": "Not enough comments to compare."}

    # 4. Set up your GPT-4o-Mini credentials
    token = os.environ.get("AIPROXY_TOKEN")

    if not token:
        return {"error": "AIPROXY_TOKEN environment variable not set."}

    openai.api_key = token
    openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

    # 5. Build a prompt enumerating all lines
    #    Ask GPT-4o-Mini to return a JSON object with "best_pair": [line1, line2]
    enumerated_lines = "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines))
    prompt = (
        "You are a helpful assistant. I have a list of comments (one per line). "
        "Please identify the TWO lines that are most semantically similar. "
        "Return your answer in JSON format as follows:\n\n"
        "{\n  \"best_pair\": [\"<comment1>\", \"<comment2>\"]\n}\n\n"
        "Here are the lines:\n\n"
        f"{enumerated_lines}\n\n"
        "Respond with only the JSON object."
    )

    try:
        # 6. Call GPT-4o-Mini with the prompt
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        # 7. Parse the raw response to extract JSON
        raw_message = response["choices"][0]["message"]["content"]
        # Remove potential markdown fences
        raw_message = re.sub(r"^```json\s*", "", raw_message.strip())
        raw_message = re.sub(r"\s*```$", "", raw_message)
        if not raw_message.strip():
            return {"error": f"LLM returned empty or invalid response: {response}"}

        data = json.loads(raw_message)
        best_pair = data.get("best_pair", [])
        if len(best_pair) != 2:
            return {"error": f"Could not find exactly 2 lines. Received: {best_pair}"}

        # 8. Write the best pair to /data/comments-similar.txt
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(best_pair[0] + "\n")
            f.write(best_pair[1] + "\n")

        return {
            "status": "success",
            "best_pair": best_pair,
            "written_file": output_file
        }

    except Exception as e:
        return {"error": str(e)}

def A10(filename='/data/ticket-sales.db', output_filename='/data/ticket-sales-gold.txt', query="SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'"):
    # Connect to the SQLite database
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    # Calculate the total sales for the "Gold" ticket type
    cursor.execute(query)
    total_sales = cursor.fetchone()[0]

    # If there are no sales, set total_sales to 0
    total_sales = total_sales if total_sales else 0

    # Write the total sales to the file
    with open(output_filename, 'w') as file:
        file.write(str(total_sales))

    # Close the database connection
    conn.close()
