import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def extract_programs(base_url):
    """Extracts the list of programs (majors/minors/certificates) and returns their names, types, and URLs"""
    response = requests.get(f"{base_url}/UGRD/programs/")
    soup = BeautifulSoup(response.text, "html.parser")

    # extract the list of programs, their urls, and types (major/minor/certificate)
    programs = []
    for div in soup.find_all("div", class_="item-container"):
        title_element = div.find("span", class_="title")
        type_element = div.find("span", class_="type")
        learn_more_link = div.find("div", class_="description").find("a")
        if title_element and type_element and learn_more_link and "href" in learn_more_link.attrs:
            program_name = title_element.text.strip()
            program_type = type_element.text.strip().replace("| UF Online", "")  # do not include UF online programs to keep things simple
            program_url = base_url + learn_more_link.attrs["href"]
            programs.append((program_name, program_type, program_url))
    return programs


def fetch_program_details(program, program_type, url, base_url):
    """Extracts the details for a given program and returns them as a dictionary"""
    program_details = {"url": base_url + url if base_url not in url else url, "type": program_type}
    response = requests.get(program_details["url"])
    soup = BeautifulSoup(response.text, "html.parser")
    program_details["main"] = soup.get_text(separator=" ", strip=True)

    # fetch each possible section
    for subsection in ["criticaltrackingtext", "modelsemesterplantext", "academiclearningcompacttext"]:
        response = requests.get(f"{program_details['url']}/#{subsection}") 
        soup = BeautifulSoup(response.text, "html.parser")
        program_details[subsection.replace("text", "")] = soup.get_text(separator=" ", strip=True)

    return program, program_details


def main():
    base_url = "https://catalog.ufl.edu"
    programs_urls = extract_programs(base_url)

    programs_details = {}
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_program_details, program, program_type, url, base_url)
                   for program, program_type, url in programs_urls]

        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Programs"):
            program, details = future.result()
            # create a unique key by combining program name and type to prevent collisions between majors & minors
            program_key = f"{program} ({details['type']})"
            programs_details[program_key] = details

    # sort the dictionary alphabetically by program name
    sorted_programs_details = dict(sorted(programs_details.items()))

    file_path = "programs_details.json"
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(sorted_programs_details, file, ensure_ascii=False, indent=4)

    print("Results saved to", file_path)

if __name__ == "__main__":
    main()
