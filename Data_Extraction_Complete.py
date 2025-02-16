import os
import glob
import time
import json
#import tempfile
import google.generativeai as genai
from PIL import Image
from pdf2image import convert_from_path
from docx2pdf import convert as docx2pdf_convert
from fpdf import FPDF
import tkinter as tk
from tkinter import filedialog


# ============================
# API key
# ============================
API_KEY = "AIzaSyC-un51IS-lC-E-JJsWVaSIb1Xg-N2Uf8Q"
genai.configure(api_key=API_KEY)


# ============================
# Initializing the Gemini model
# ============================
model = genai.GenerativeModel("gemini-1.5-flash")


# ============================
# Directory user input and defining supported file types
# ============================
root = tk.Tk()
root.withdraw()  # Hide the main window
print("Select the folder containing the files")
INPUT_FOLDER = filedialog.askdirectory(title="Select the folder containing the files")
if not INPUT_FOLDER:
    print("No folder selected. Exiting.")
    exit(1)

image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
docx_exts  = {".docx"}
txt_exts   = {".txt"}
pdf_exts   = {".pdf"}


# ============================
# Poppler Path
# ============================
poppler_path = r"C:\poppler\poppler-24.08.0\Library\bin"

converted_images = []

# ============================
# Pdf to Images
# ============================
def convert_pdf_to_images(pdf_path):
    """
    Converts a PDF file to images using pdf2image.
    """
    try:
        images = convert_from_path(pdf_path, dpi=200, poppler_path=poppler_path)
        base_name = os.path.splitext(pdf_path)[0]
        for idx, image in enumerate(images, start=1):
            output_filename = f"{base_name}-{idx}.jpg"
            image.save(output_filename, "JPEG")
            converted_images.append(output_filename)  # Store converted image path
        print(f"Converted '{pdf_path}' to {len(images)} image(s).")
    except Exception as e:
        print(f"Error converting PDF '{pdf_path}': {e}")


# ============================
# Docx to Images
# ============================
def convert_docx_to_images(docx_path):
    """
    Converts a DOCX file to images.
    """
    try:
        pdf_path = os.path.splitext(docx_path)[0] + ".pdf"
        docx2pdf_convert(docx_path, os.path.dirname(docx_path))
        convert_pdf_to_images(pdf_path)
        os.remove(pdf_path)  # Cleanup intermediate PDF
    except Exception as e:
        print(f"Error converting DOCX '{docx_path}': {e}")


# ============================
# Txt to Images
# ============================
def convert_txt_to_images(txt_path):
    """
    Converts a TXT file to images by first converting it to a PDF.
    """
    try:
        pdf_path = os.path.splitext(txt_path)[0] + ".pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Set a Unicode-compatible font (DejaVu Sans or FreeSans)
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.set_font("DejaVu", "", 12)

        with open(txt_path, "r", encoding="utf-8-sig") as file:  # Ensure UTF-8 encoding
            for line in file:
                pdf.multi_cell(0, 10, line)

        pdf.output(pdf_path)
        convert_pdf_to_images(pdf_path)
        os.remove(pdf_path)  # Cleanup intermediate PDF
    except Exception as e:
        print(f"Error converting TXT '{txt_path}': {e}")


#==================================================================================================
#==================================================================================================


def process_files():
    """
    Convert non-image files to images.
    """
    files = glob.glob(os.path.join(INPUT_FOLDER, "*"))
    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in pdf_exts:
            convert_pdf_to_images(file_path)
        elif ext in docx_exts:
            convert_docx_to_images(file_path)
        elif ext in txt_exts:
            convert_txt_to_images(file_path)
        elif ext in image_exts:
            continue  # Already an image, do nothing
        else:
            print(f"Skipping unsupported file type: {file_path}")


def extract_text_from_images():
    """
    Extract text from all images and send to Gemini.
    """
    all_files = glob.glob(os.path.join(INPUT_FOLDER, "*"))
    aggregated_text = ""
    
    for file_path in all_files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in image_exts:
            try:
                img = Image.open(file_path)
            except Exception as e:
                print(f"Error opening image {file_path}: {e}")
                continue

            ocr_prompt = (
                "Extract all text from this image accurately. "
                "Return only the text as it appears. "
                "Do not include any extra information. "
                "Wrap the extracted text within [Start of File] and [End of File]."
            )
            
            try:
                response = model.generate_content([ocr_prompt, img])
                file_text = response.text.strip()
            except Exception as e:
                print(f"Error extracting text from image {file_path}: {e}")
                continue
            
            img.close()
            time.sleep(5)  # Avoid rate limiting
            aggregated_text += f"--- Filename: {os.path.basename(file_path)} ---\n{file_text}\n\n"

    return aggregated_text


# ============================
# Generating JSON file
# ============================
'''
def generate_json_profile(aggregated_text):
    """
    Send extracted text to Gemini for structured JSON output.
    """
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
    
    retry_attempts = 3
    json_output = ""
    for attempt in range(retry_attempts):
        try:
            profile_response = model.generate_content(profile_prompt)
            json_text = profile_response.text.strip()
            json_start = json_text.find('{')
            json_end = json_text.rfind('}') + 1
            json_text = json_text[json_start:json_end]
            json_output = json.loads(json_text)
            break
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Invalid JSON response, retrying... (Attempt {attempt+1}/{retry_attempts})")
            time.sleep(5)
    if not json_output:
        json_output = {"profiles": []}
    return json_output
'''


def clean_json_response(response_text):
    """
    Cleans and extracts valid JSON from Gemini's response.
    Ensures removal of unnecessary formatting such as triple backticks.
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
    Uses retries and ensures valid JSON formatting.
    """
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

    retry_attempts = 3  # Retries added for reliability
    json_output = ""

    for attempt in range(retry_attempts):
        try:
            profile_response = model.generate_content(profile_prompt)
            json_text = profile_response.text.strip()

            # Use the cleaning function before parsing JSON
            cleaned_json_text = clean_json_response(json_text)

            # Parse JSON after cleaning
            json_output = json.loads(cleaned_json_text)
            break  # Success, exit retry loop

        except json.JSONDecodeError as e:
            print(f"Invalid JSON response, retrying... (Attempt {attempt+1}/{retry_attempts})")
            time.sleep(5)  # Delay before retrying to avoid API rate limits

    if not json_output:
        json_output = {"profiles": []}  # Return empty profiles if parsing fails

    return json_output


#============____main_____==============

def main():
    global converted_images  # Ensure we access the global list
    process_files()
    extracted_text = extract_text_from_images()
    json_data = generate_json_profile(extracted_text)

    output_file = "Extracted_Data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    print(f"All extracted profiles have been saved to {output_file}")

    # Delete only the converted images
    time.sleep(1)
    for image_path in converted_images:
        try:
            os.remove(image_path)
            print(f"Deleted converted image: {image_path}")
        except Exception as e:
            print(f"Error deleting {image_path}: {e}")

if __name__ == "__main__":
    main()