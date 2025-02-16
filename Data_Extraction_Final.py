# https://github.com/oschwartz10612/poppler-windows/releases
# pip install google-generativeai pillow pdf2image docx2pdf fpdf glob2
# poppler_path = r"C:\poppler\poppler-24.08.0\Library\bin" 

import os
import glob
import time
import json
import tempfile
import shutil
import google.generativeai as genai
from PIL import Image
from pdf2image import convert_from_path
from docx2pdf import convert as docx2pdf_convert
from fpdf import FPDF

# ============================
# Step 1: Set up your API key
# ============================
API_KEY = "AIzaSyC-un51IS-lC-E-JJsWVaSIb1Xg-N2Uf8Q"
genai.configure(api_key=API_KEY)

# ============================
# Step 2: Initialize the Gemini model
# ============================
model = genai.GenerativeModel("gemini-1.5-flash")

# ============================
# Step 3: Get the user input for directory
# ============================
INPUT_FOLDER = input("Enter the path to the directory containing the files: ").strip()
if not os.path.exists(INPUT_FOLDER):
    print("Error: The specified directory does not exist.")
    exit(1)

image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
docx_exts  = {".docx"}
txt_exts   = {".txt"}
pdf_exts   = {".pdf"}

poppler_path = r"C:\poppler\poppler-24.08.0\Library\bin"  # Update with your actual Poppler bin path or set to None if Poppler is in PATH

def convert_pdf_to_images(pdf_path, temp_dir):
    """
    Converts a PDF file to images using pdf2image.
    """
    try:
        images = convert_from_path(pdf_path, dpi=200, poppler_path=poppler_path)
        for idx, image in enumerate(images, start=1):
            output_filename = os.path.join(temp_dir, f"{os.path.basename(pdf_path)}-{idx}.jpg")
            image.save(output_filename, "JPEG")
    except Exception as e:
        print(f"Error converting PDF '{pdf_path}': {e}")

def convert_docx_to_images(docx_path, temp_dir):
    """
    Converts a DOCX file to images.
    """
    try:
        with tempfile.TemporaryDirectory() as temp_pdf_dir:
            pdf_path = os.path.join(temp_pdf_dir, "temp.pdf")
            docx2pdf_convert(docx_path, temp_pdf_dir)
            convert_pdf_to_images(pdf_path, temp_dir)
    except Exception as e:
        print(f"Error converting DOCX '{docx_path}': {e}")

def convert_txt_to_images(txt_path, temp_dir):
    """
    Converts a TXT file to images by first converting it to a PDF.
    """
    try:
        with tempfile.TemporaryDirectory() as temp_pdf_dir:
            pdf_path = os.path.join(temp_pdf_dir, "temp.pdf")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            with open(txt_path, "r", encoding="utf-8") as file:
                for line in file:
                    pdf.multi_cell(0, 10, line)
            pdf.output(pdf_path)
            convert_pdf_to_images(pdf_path, temp_dir)
    except Exception as e:
        print(f"Error converting TXT '{txt_path}': {e}")

def process_files(temp_dir):
    """
    Convert non-image files to images.
    """
    files = glob.glob(os.path.join(INPUT_FOLDER, "*"))
    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in pdf_exts:
            convert_pdf_to_images(file_path, temp_dir)
        elif ext in docx_exts:
            convert_docx_to_images(file_path, temp_dir)
        elif ext in txt_exts:
            convert_txt_to_images(file_path, temp_dir)
        elif ext in image_exts:
            shutil.copy(file_path, temp_dir)  # Copy existing images to temp dir
        else:
            print(f"Skipping unsupported file type: {file_path}")

def extract_text_from_images(temp_dir):
    """
    Extract text from all images and send to Gemini.
    """
    all_files = glob.glob(os.path.join(temp_dir, "*"))
    aggregated_text = ""
    
    for file_path in all_files:
        try:
            img = Image.open(file_path)
            ocr_prompt = (
                "Extract all text from this image accurately. "
                "Return only the text as it appears. "
                "Do not include any extra information. "
                "Wrap the extracted text within [Start of File] and [End of File]."
            )
            response = model.generate_content([ocr_prompt, img])
            if response and hasattr(response, 'text') and response.text.strip():
                file_text = response.text.strip()
                aggregated_text += f"--- Filename: {os.path.basename(file_path)} ---\n{file_text}\n\n"
            else:
                print(f"Warning: Empty response from Gemini for {file_path}")
        except Exception as e:
            print(f"Error extracting text from image {file_path}: {e}")
        time.sleep(4)  # Avoid rate limiting
    return aggregated_text

def clean_json_response(response_text):
    """
    Cleans and extracts valid JSON from Gemini's response.
    """
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]  # Remove ```json
    if response_text.endswith("```"):
        response_text = response_text[:-3]  # Remove closing ```
    return response_text.strip()

def generate_json_profile(aggregated_text):
    """
    Send extracted text to Gemini for structured JSON output.
    """
    if not aggregated_text.strip():
        print("No extracted text to process.")
        return {"profiles": []}
    profile_prompt = f"""
You are an AI specialized in extracting and structuring data from documents in both English and Bangla/Bengali. Your task is to analyze the extracted text from multiple images, identify different individuals mentioned, and extract their relevant details in a structured JSON format.

## **Expected JSON Output Structure**
You must return the extracted details in a **strictly valid structured JSON format**. Below is an example of how the data should be structured:
```json
{{    
    "profiles": [
        {{
            "name": "আলেক্সিস বুল",
            "age": "৩৫",
            "date_of_birth": "১২ জুন, ১৯৮৯",
            "gender": "Female",
            "contact_info": "alexis.bull@example.com",
            "address": {{
                "street": "200 Sporting Green",
                "city": "South San Francisco",
                "state": "CA",
                "zipCode": 99236,
                "country": "United States of America"
            }},
            "phone_numbers": [
                {{
                    "type": "Office",
                    "number": "909-555-7307"
                }},
                {{
                    "type": "Mobile",
                    "number": "415-555-1234"
                }}
            ],
            "education": "Master's in Business Administration",
            "work_experience": "Procurement Manager at XYZ Corp",
            "purchase_order": [
                {{
                    "PONumber": 1600,
                    "Reference": "ABULL-20140421",
                    "Requestor": "Alexis Bull",
                    "User": "ABULL",
                    "CostCenter": "A50",
                    "ShippingInstructions": {{
                        "name": "Alexis Bull",
                        "Address": {{
                            "street": "200 Sporting Green",
                            "city": "South San Francisco",
                            "state": "CA",
                            "zipCode": 99236,
                            "country": "United States of America"
                        }},
                        "Phone": [
                            {{
                                "type": "Office",
                                "number": "909-555-7307"
                            }},
                            {{
                                "type": "Mobile",
                                "number": "415-555-1234"
                            }}
                        ]
                    }},
                    "Special Instructions": null,
                    "AllowPartialShipment": false,
                    "LineItems": [
                        {{
                            "ItemNumber": 1,
                            "Part": {{
                                "Description": "One Magic Christmas",
                                "UnitPrice": 19.95,
                                "UPCCode": 13131092899
                            }},
                            "Quantity": 9.0
                        }},
                        {{
                            "ItemNumber": 2,
                            "Part": {{
                                "Description": "Lethal Weapon",
                                "UnitPrice": 19.95,
                                "UPCCode": 85391628927
                            }},
                            "Quantity": 5.0
                        }}
                    ]
                }}
            ]
        }}
    ]
}}
```

## **Task Breakdown:**  
1. **Identify Individuals:**  
   - Extract relevant personal details (e.g., name, father's name, mothers name, age, date of birth, gender, address, phone numbers, etc.). You have to think carefully and logically as there can be various and different kinds of key and value pair ( "key": "value" ) which can be considered as user data. 
   - If multiple individuals exist, structure them under the `"profiles"` array.

2. **Ensure Data Structuring:**  
   - The extracted information must be formatted using key-value pairs, JSON arrays, and nested objects where appropriate.  
   - Data relationships should be preserved (e.g., phone numbers should be linked to the correct individual).  
   - Ensure consistency across structured profiles.  

3. **Handling English and Bangla/Bengali Text:**  
   - If a **key** is found in Bangla/Bengali, translate it to English while preserving the Bangla/Bengali **value**.  
   - If an English **key** has a Bangla/Bengali **value**, **do not** translate the value.  

4. **Handling Missing or Incomplete Data:**  
   - If a certain detail is missing but should logically be a key, **include the key** and set its value as `"Not Available"`.  
   - Do not make assumptions; only extract what is explicitly present.  

5. **Expected JSON Structure:**  
   - The response **must** be a valid JSON object.  
   - If no structured data is found, return an empty `"profiles"` array.

Here is the extracted content:
<<<
{aggregated_text}
>>>
"""
    
    try:
        profile_response = model.generate_content(profile_prompt)
        cleaned_response = clean_json_response(profile_response.text.strip())
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return {"profiles": []}
    except Exception as e:
        print(f"Error generating JSON profile: {e}")
        return {"profiles": []}

def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        process_files(temp_dir)
        extracted_text = extract_text_from_images(temp_dir)
        json_data = generate_json_profile(extracted_text)
        output_file = os.path.join(INPUT_FOLDER, "Extracted_Data.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        print(f"All extracted profiles have been saved to {output_file}")

if __name__ == "__main__":
    main()