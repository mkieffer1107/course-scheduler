import os
import json
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool, Manager
import tqdm

def fetch_major_courses(args):
    major, url, base_url, majors_courses_proxy = args
    major_response = requests.get(base_url + url)
    major_soup = BeautifulSoup(major_response.text, "html.parser")
    
    courses = []
    
    course_blocks = major_soup.find_all("div", class_="courseblock")
    for course_block in course_blocks:
        course_title = course_block.find("p", class_="courseblocktitle")
        
        if course_title:
            course_code_name = course_title.find("strong").text.strip()
            course_code, course_name = course_code_name.split(" ", 1)
            course_credits = course_title.find("span", class_="credits").text.strip()
            course_description = course_block.find("p", class_="courseblockdesc").text.strip()
            
            prerequisites = []
            grading_scheme = ""
            
            course_extras = course_block.find_all("p", class_="courseblockextra noindent")
            for extra in course_extras: 
                if "Prerequisite:" in extra.text:                     # TODO: consider cases like "junior or senior standing" or "permission of instructor"
                    for prereq_link in extra.find_all("a"): 
                        prereq_text = prereq_link.text.strip()
                        prereq_code = prereq_text.replace("\xa0", " ")  # replace non-breaking spaces
                        prerequisites.append(prereq_code)
                elif "Grading Scheme:" in extra.text:
                    grading_scheme = extra.text.replace("Grading Scheme:", "").strip()
            
            course_info = {
                "code": course_code,
                "name": course_name,
                "credits": course_credits,
                "description": course_description,
                "prerequisites": prerequisites,
                "grading_scheme": grading_scheme
            }
            
            courses.append(course_info)
    
    majors_courses_proxy[major] = courses



def main():
    base_url = "https://catalog.ufl.edu"
    
    response = requests.get(base_url + "/UGRD/courses/")
    html_content = response.text
    
    soup = BeautifulSoup(html_content, "html.parser")
    nav_menu = soup.find("nav", id="cl-menu")
    
    # get a list of majors and their URLs in form of [(major, url), ...]
    majors_urls = []
    for li in nav_menu.find_all("li"):
        a_element = li.find("a")
        if a_element:
            major = a_element.text.strip()
            url = a_element["href"]
            majors_urls.append((major, url))
    
    # fetch courses for each major
    manager = Manager()
    majors_courses = manager.dict()
    pool_args = [(major, url, base_url, majors_courses) for major, url in majors_urls]
    
    with Pool(processes=4) as pool:
        list(tqdm.tqdm(pool.imap_unordered(fetch_major_courses, pool_args), total=len(pool_args), desc="Processing Courses"))
    
    # convert the manager dict to a regular dict and sort it alphabetically by major names
    majors_courses_dict = dict(sorted(majors_courses.items()))

    out_dir = "."
    file_path = os.path.join(out_dir, "courses.json")
    with open("courses.json", "w", encoding="utf-8") as file:
        json.dump(majors_courses_dict, file, ensure_ascii=False, indent=4)
    
    print("Results saved to", file_path)

if __name__ == "__main__":
    main()
