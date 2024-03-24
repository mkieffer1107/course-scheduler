import json
import random
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

NUM_SCHEDULE_OPTIONS = 5

def generate_schedules(course_credits, num_schedule_options=5):
    """Generate possible schedules for a list of courses."""
    credit_hours = int(course_credits)
    num_schedule_options = NUM_SCHEDULE_OPTIONS or num_schedule_options # gross... I know. don't want to pass into multiprocessing :p

    schedules = []
    if credit_hours in [1, 2, 3]:
        # MWF class, single period each day at same time
        for _ in range(num_schedule_options):
            period = random.choice(range(1, 12))  # periods 1-11
            schedules.append({"MWF": period})
    elif credit_hours == 4:
        # TR class, Tuesday one period, Thursday two contiguous periods, not necessarily same time
        for _ in range(num_schedule_options):
            period_t = random.choice(range(1, 12))  # periods 1-11
            period_r = random.choice(range(1, 11))  # periods 1-10 to save room for double period
            schedules.append({
                "T": period_t,
                "R": [period_r, period_r + 1]  # Two contiguous periods on Thursday
            })

    return schedules


def fetch_major_courses(major, url, base_url):
    """Extracts the list of courses for a given major and returns their details"""
    major_response = requests.get(base_url + url)
    major_soup = BeautifulSoup(major_response.text, "html.parser")
    courses = []

    # get the course info for each course in the major
    for course_block in major_soup.find_all("div", class_="courseblock"):
        course_title = course_block.find("p", class_="courseblocktitle")
        if course_title:
            course_code_name = course_title.find("strong").text.strip()
            course_code, course_name = course_code_name.split(" ", 1)
            course_description = course_block.find("p", class_="courseblockdesc").text.strip()
            
            # remove the suffix "Credits" or "Credit" -- do plural first to avoid removing "Credit" from "Credits"
            course_credits = course_title.find("span", class_="credits") \
                .text \
                .replace("Credits", "").strip() \
                .replace("Credit", "").strip() 
        
            # if course credits has form like "0-3" then take the second number
            if "-" in course_credits:
                course_credits = course_credits[-1]

            # handle prerequisites and grading scheme
            prerequisites = []   # store list of prerequisites     TODO: handle "junior or senion standing" etc.  or ignore :)
            grading_scheme = ""
            for extra in course_block.find_all("p", class_="courseblockextra noindent"):
                if "Prerequisite:" in extra.text:
                    prerequisites = [prereq_link.text.strip().replace("\xa0", " ") for prereq_link in extra.find_all("a")]
                elif "Grading Scheme:" in extra.text:
                    grading_scheme = extra.text.replace("Grading Scheme:", "").strip()

            # build dict to store info
            course_info = {
                "code": course_code,
                "name": course_name,
                "credits": course_credits,
                "description": course_description,
                "prerequisites": prerequisites,
                "grading_scheme": grading_scheme,
                "schedules": generate_schedules(course_credits)
            }
            courses.append(course_info)

    return major, url, courses


def main():
    base_url = "https://catalog.ufl.edu"
    response = requests.get(base_url + "/UGRD/courses/")
    soup = BeautifulSoup(response.text, "html.parser")
    nav_menu = soup.find("nav", id="cl-menu")

    # get a list of the majors and their URLs (well it's really not just majors... oh well)
    majors_urls = []
    for a_element in nav_menu.find_all("a"):
        major = a_element.text.strip()
        url = a_element["href"]
        majors_urls.append((major, url))

    # fetch the courses for each major in parallel
    majors_courses = {}
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_major_courses, major, url, base_url) for major, url in majors_urls]

        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Courses by Major"):
            major, url, courses = future.result()
            majors_courses[major] = {
                "url": base_url + url,
                "courses": courses
            }
    
    # sort the dictionary alphabetically by major name
    majors_courses_sorted = dict(sorted(majors_courses.items()))

    with open("courses.json", "w", encoding="utf-8") as file:
        json.dump(majors_courses_sorted, file, ensure_ascii=False, indent=4)

    print("Results saved to courses.json")
    print("Number of total course categories:", len(majors_courses))
    print("Number of total courses:", sum([len(majors_courses[major]["courses"]) for major in majors_courses]))
    print("Number of total schedulings:", sum([len(majors_courses[major]["courses"]) for major in majors_courses]) * NUM_SCHEDULE_OPTIONS)

if __name__ == "__main__":
    main()