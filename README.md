# course-scheduler
UF Open Source Club’s 24-hour mini-hack submission


When scheduling classes, it is extremely annoying to transition between
the degree audit page, the course scheduler, and the major course list,
elective course list, etc. This project aims to integrate all of these
features into a single chatbot as an example for a service that UF could
offer to all students. This would help aid in UF's goal of buliding an
AI university!

Keep in mind that this is a demo built in roughly 10 hours by students
without the vast resources and up-to-date schedules of America's first
AI university! Enjoy <3
---

## Working with Conda

Set up Conda Environment

```sh
conda create --name scheduler python=3.9 -y
conda activate scheduler
pip install -r requirements.txt
```

Delete Conda Environment

```sh
conda deactivate
conda env remove --name scheduler
```

---

## References and Data Sources

The following resources were referenced or reappropriated in this project:

| Resource | Description | Link |
|----------|-------------|------|
| Course Catalog by Major | A complete listing of courses available by major at UF. | [View Catalog](https://catalog.ufl.edu/UGRD/courses/) |
| Course Catalog with Search (Not Used) | An alternative course catalog offering search functionality. | [Search Courses](https://catalog.ufl.edu/course-search/) |
| 2023-2024 Undergraduate Catalog | The official UF undergraduate catalog for the academic years 2023-2024. | [View PDF](https://catalog.ufl.edu/pdf/2023-2024%20Undergraduate%20Catalog%20UF.pdf) |
| Major and Minor Requirements | Detailed requirements for majors and minors offered at UF. | [View Requirements](https://catalog.ufl.edu/UGRD/programs/) |

Please note that some resources may not be used directly in the project but are included for completeness (thank u, Claude <3).
