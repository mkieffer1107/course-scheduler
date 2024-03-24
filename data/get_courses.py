import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

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
            course_credits = course_title.find("span", class_="credits").text.strip()
            course_description = course_block.find("p", class_="courseblockdesc").text.strip()

            # handle prerequisites and grading scheme
            prerequisites = []   # store list of prerequisites     TODO: handle "junior or senion standing" etc.
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
                "grading_scheme": grading_scheme
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


if __name__ == "__main__":
    main()