
from typing_extensions import LiteralString
import fitz  # PyMuPDF for text extraction
import os,re
import shutil
from unidecode import unidecode # type: ignore[attr-defined]


# Root directory containing PDFs
# TODO: This needs to be somewhere where it is installed later
root_path = "/Users/markoristic/open-source/racunko/downloads"

file_paths= ["informatika", "eps"]


# List all files in the root path, excluding subdirectories
def extract(cache):
    # extract to is file where end will be downloads/PERIOD 
    PERIOD = f"{cache['year']}_{cache['month']}"
    extract_to = f"{root_path}/{PERIOD}"
    os.makedirs(extract_to, exist_ok=True)

    # Store extracted data for sorting
    entries = []

    for folder_name in file_paths:
        full_path = os.path.join(root_path, folder_name)


        for file_name in os.listdir(full_path):
            file_path = os.path.join(full_path, file_name)

            if os.path.isfile(file_path) and file_name.endswith(".pdf"):
                doc = fitz.open(file_path)
                text = "\n".join([page.get_text("text") for page in doc]) # type: ignore[attr-defined]
                lines = text.split("\n")
                loc_adress = ""
                file_name = ""
                value = ""
                if folder_name == "eps":
                    loc_adress, file_name, value = process_eps_file(lines)
                elif folder_name == "informatika":
                    loc_adress, file_name, value = process_informatika_file(lines)
                else:
                    print("\n\nNOT IMPLEMENTED \n\n")
                
                # Store entry if valid
                if file_name and loc_adress:
                    entries.append(value)
                    # Ensure directory exists
                    destination_dir = os.path.join(extract_to, loc_adress)
                    os.makedirs(destination_dir, exist_ok=True)
                    
                    # Create the destination path
                    destination_file_path = os.path.join(destination_dir, f"{file_name}.pdf")
                    
                    # Copy file with unique name
                    shutil.copy(file_path, destination_file_path)
                    print(f"✅ File copied to: {destination_file_path}")
                    
                    # Remove original file
                    os.remove(file_path)
                    print(f"❌ Removed original file: {file_path}")

        # Print sorted output
        for entry in entries:
            print(entry)

def process_eps_file(lines: list[LiteralString]):
    loc_adress = ""
    file_name = ""
    value = ""
    if lines[0] == "ДУПЛИКАТ":
        address_line = ""
        for i, line in enumerate(lines):
            found_adress = False
            found_value = False
            if "Адреса мерног места" in line and not found_adress:
                address_line = lines[i + 2]
                loc = unidecode(address_line).lower()
                app_num = loc.split()[-1]
                file_name= f"eps_{app_num}"
                loc_adress = "_".join(loc.split()[:-1])
                found_adress = True
            if "ЗА УПЛАТУ ЗА ЕЛЕКТРИЧНУ ЕНЕРГИЈУ (А+Б)" in line and not found_value:
                value_num = lines[i+1].lstrip()
                value = f"{address_line} - {value_num}"
                found_value = True
            if found_adress and found_value:
                break
    else:
        for i, line in enumerate(lines):
            if "ПОТРОШЊА У ОБРАЧУНСКОМ ПЕРИОДУ" in line:
                address_line = lines[i + 4]
                loc = unidecode(address_line).lower()
                app_num_line = lines[i+5]
                app_num = app_num_line.split()[-1]
                file_name= f"eps_{app_num}"
                loc_adress = "_".join(loc.split())
                value_num = lines[i+6].lstrip()
                value = f"{address_line} - {value_num}"

    # print(loc_adress)
    # print(file_name)
    # print(value)
    return loc_adress, file_name, value

def process_informatika_file(lines: list[LiteralString]):
    loc_adress = ""
    file_name = ""
    value = ""
    # NOTE: This is informatika apartment
    if "Поштарина плаћена код поште" in lines[0]:
        for i, line in enumerate(lines):
            if "НАПОМЕНА О ПОРЕСКОМ ОСЛОБОЂЕЊУ" in line:
                address_line = lines[i+9]
                value = f"{address_line} - {lines[i+7].strip()}"
                match = re.match(r"^(.*?)\s*\([^,]+,([^)\n]+)\)", address_line)
                if match:
                    loc_adress = "_".join(unidecode(match.group(1).strip()).lower().split())
                    loc_app_num = unidecode(match.group(2).strip().lower())
                    file_name = f"informatika_{loc_app_num}"
                else:
                    print("No match found")
                break 

    # NOTE: Then it must be garage
    else:
        address_line = lines[5]
        match = re.match(r"^(.*?)\s*\([^,]+,([^)\n]+)\)", address_line)
        if match:
            loc_adress = "_".join(unidecode(match.group(1).strip()).lower().split())
            loc_garage_num = unidecode(match.group(2).strip().lower())
            file_name = f"informatika_{loc_garage_num}"
        else:
            print("No match found")
        for i, line in enumerate(lines):
            if "УКУПНО ЗА УПЛАТУ" in line:
                value_num = lines[i+1].strip()
                value = f"{address_line} - {value_num}"
                break

    # print(loc_adress)
    # print(file_name)
    # print(value)
    return loc_adress, file_name, value


