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
            program_type = type_element.text.strip().replace("| UF Online", "").strip()  # do not include UF online programs to keep things simple


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

# def fetch_program_details(program, program_type, url, base_url):
#     """Extracts the details for a given program and returns them as a dictionary"""
#     program_details = {"url": base_url + url if base_url not in url else url, "type": program_type}

#     response = requests.get(program_details["url"])
#     soup = BeautifulSoup(response.text, "html.parser")

#     course_tables = soup.find_all("table", class_="sc_courselist")
#     program_details["courses"] = []

#     current_area = None
#     courses_by_area = {}

#     for table in course_tables:
#         rows = table.find_all("tr")
#         for row in rows:
#             if "areaheader" in row.get("class", []):
#                 current_area = row.find("span", class_="courselistcomment").text.strip()
#                 courses_by_area[current_area] = []
#             else:
#                 cols = row.find_all("td")
#                 if len(cols) >= 2:
#                     course_code = cols[0].text.strip()
#                     if course_code and current_area:
#                         courses_by_area[current_area].append(course_code)

#     program_details["courses"] = courses_by_area

#     return program, program_details

# def fetch_program_details(program, program_type, url, base_url):
#     """Extracts the details for a given program and returns them as a dictionary"""
#     program_details = {"url": base_url + url if base_url not in url else url, "type": program_type}

#     for subsection in ["criticaltrackingtext", "modelsemesterplantext", "academiclearningcompacttext"]:
#         response = requests.get(f"{program_details['url']}/#{subsection}")
#         soup = BeautifulSoup(response.text, "html.parser")
        
#         possible_classes = ["sc_plangrid", "sc_courselist"]
#         course_tables = soup.find_all("table", class_="sc_courselist")
#         subsection_courses = {}

#         current_area = None
#         courses_by_area = {}

#         for table in course_tables:
#             rows = table.find_all("tr")
#             for row in rows:
#                 if "areaheader" in row.get("class", []):
#                     current_area = row.find("span", class_="courselistcomment").text.strip()
#                     courses_by_area[current_area] = []
#                 else:
#                     cols = row.find_all("td")
#                     if len(cols) >= 2:
#                         course_code = cols[0].text.strip()
#                         if course_code and current_area:
#                             courses_by_area[current_area].append(course_code)

#         subsection_courses = courses_by_area
#         program_details[subsection.replace("text", "")] = subsection_courses

#     return program, program_details


# courtesy of our friend Claude <3
def fetch_program_details(program, program_type, url, base_url):
    """Extracts the details for a given program and returns them as a dictionary"""
    program_details = {"url": base_url + url if base_url not in url else url, "type": program_type}

    for subsection in ["criticaltrackingtext", "modelsemesterplantext", "academiclearningcompacttext"]:
        response = requests.get(f"{program_details['url']}/#{subsection}")
        soup = BeautifulSoup(response.text, "html.parser")

        # UF uses at least 4 different classes for tables in their course catalog
        dumb_table_classes = [f"sc_sctable tbl_academiclearningcompact{i}" for i in range(1, 6)]
        table_classes = ["sc_courselist", "sc_plangrid"] + dumb_table_classes
        course_tables = soup.find_all(["table", {"class": tbl_class}] for tbl_class in table_classes)

        subsection_courses = {}

        for table in course_tables:
            if "sc_courselist" in table.get("class", []):
                # Handle sc_courselist table
                rows = table.find_all("tr")
                has_area_header = any("areaheader" in row.get("class", []) for row in rows)

                if has_area_header:
                    current_area = None
                    courses_by_area = {}

                    for row in rows:
                        if "areaheader" in row.get("class", []):
                            current_area = row.find("span", class_="courselistcomment").text.strip()
                            courses_by_area[current_area] = []
                        else:
                            cols = row.find_all("td")
                            if len(cols) >= 2:
                                course_code = cols[0].text.strip()
                                if course_code and current_area:
                                    courses_by_area[current_area].append(course_code)

                    subsection_courses.update(courses_by_area)
                else:
                    courses = []

                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            course_code = cols[0].text.strip()
                            if course_code:
                                courses.append(course_code)

                    subsection_courses["courses"] = courses
            elif "sc_plangrid" in table.get("class", []):
                # Handle sc_plangrid table
                current_semester = None
                courses_by_semester = {}

                rows = table.find_all("tr")
                for row in rows:
                    if "plangridterm" in row.get("class", []):
                        current_semester = row.find("th").text.strip()
                        courses_by_semester[current_semester] = []
                    else:
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            course_code = cols[0].text.strip()
                            if course_code and current_semester:
                                courses_by_semester[current_semester].append(course_code)
                            else:
                                course_comment = row.find("span", class_="comment")
                                if course_comment and current_semester:
                                    courses_by_semester[current_semester].append(course_comment.text.strip())

                subsection_courses.update(courses_by_semester)
            elif any(f"sc_sctable tbl_academiclearningcompact{i}" in table.get("class", []) for i in range(1, 6)):
                # Handle academic learning compact tables
                rows = table.find_all("tr")
                courses = []

                for row in rows[1:]:  # Skip the header row
                    cols = row.find_all("td")
                    if len(cols) >= 1:
                        course_code = cols[0].text.strip()
                        if course_code:
                            courses.append(course_code)

                subsection_courses["courses"] = courses

        program_details[subsection.replace("text", "")] = subsection_courses

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

    file_path = "programs.json"
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(sorted_programs_details, file, ensure_ascii=False, indent=4)

    print("Results saved to", file_path)


if __name__ == "__main__":
    main()



'''
Traceback (most recent call last):
  File "/Users/mkieffer/programming/ml/course-scheduler/data/get_degrees.py", line 190, in <module>
    main()
  File "/Users/mkieffer/programming/ml/course-scheduler/data/get_degrees.py", line 174, in main
    program, details = future.result()
  File "/Users/mkieffer/miniforge3/envs/scheduler/lib/python3.9/concurrent/futures/_base.py", line 439, in result
    return self.__get_result()
  File "/Users/mkieffer/miniforge3/envs/scheduler/lib/python3.9/concurrent/futures/_base.py", line 391, in __get_result
    raise self._exception
  File "/Users/mkieffer/miniforge3/envs/scheduler/lib/python3.9/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
  File "/Users/mkieffer/programming/ml/course-scheduler/data/get_degrees.py", line 151, in fetch_program_details
    courses_by_semester[current_semester].append(course_code)
KeyError: None
(scheduler) mkieffer@
'''