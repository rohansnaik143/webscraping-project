# webscraping-project
Python scraper for Wellfound.com jobs (UK-based). Extracts company name, job title, location, salary, and apply link from static content, and fetches job descriptions dynamically using Selenium. Data is stored in PostgreSQL, with nulls for missing descriptions.



## Requirements
- Python 3.10+
- PostgreSQL installed and running
- Google Chrome browser installed



#pip install -r requirements.txt



#Setup PostgreSQL Database
Create a database (e.g., internship_assessment).
Create the table:


  CREATE TABLE job_listings (
    id SERIAL PRIMARY KEY,
    job_title TEXT,
    company_name TEXT,
    location TEXT,
    salary_info TEXT,
    job_url TEXT UNIQUE,
    source_site TEXT,
    job_description TEXT
);




#Update the database connection in scraper.py:
#conn = psycopg2.connect(
    dbname="internship_assessment",
    user="your_user",
    password="your_password",
    host="localhost",
    port="5432"
)



#Run the script
python scraper.py

