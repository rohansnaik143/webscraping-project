import psycopg2
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


# Database Setup

def connect_db():
    conn = psycopg2.connect(
        dbname="internship_assessment",
        user="your_username",
        password="your_password",
        host="localhost",
        port="5432"
    )
    return conn, conn.cursor()


# Scrape static job data

def scrape_static_jobs(html_snippets):
    jobs_data = []

    for snippet in html_snippets:
        soup = BeautifulSoup(snippet["html"], "html.parser")

        # Company Name
        company_tag = soup.find("h2")
        company_name = company_tag.get_text(strip=True) if company_tag else None

        # Job Title
        job_tag = soup.find("h4")
        job_title = job_tag.get_text(strip=True) if job_tag else None

        # Location
        location_tag = soup.find("span", {"data-testid": "location-display"})
        location = location_tag.get_text(strip=True) if location_tag else None

        # Salary
        salary_tag = soup.find("span", class_="styles_compensation__DUzmb")
        if not salary_tag:
            salary_tag = soup.find("span", class_="styles_compensation__3JnvU")
        salary = salary_tag.get_text(strip=True) if salary_tag else None

        # Apply Link
        link_tag = soup.find("a", href=True, class_="styles-module_component__88XzG")
        job_url = f"https://wellfound.com{link_tag['href']}" if link_tag else None

        jobs_data.append({
            "company_name": company_name,
            "job_title": job_title,
            "location": location,
            "salary_info": salary,
            "job_url": job_url,
            "source_site": snippet["source"]
        })
    return jobs_data


# Insert jobs into DB

def insert_jobs(cursor, conn, jobs_data):
    for job in jobs_data:
        try:
            cursor.execute("""
                INSERT INTO job_listings (job_title, company_name, location, job_url, salary_info, source_site)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_url) DO NOTHING
            """, (job["job_title"], job["company_name"], job["location"], job["job_url"], job["salary_info"], job["source_site"]))
            print(f"Inserted: {job['company_name']} - {job['job_title']}")
        except Exception as e:
            print(f"Error inserting {job['company_name']} - {job['job_title']}: {e}")
    conn.commit()


# Scrape dynamic job descriptions

def scrape_job_descriptions(cursor, conn):
    cursor.execute("SELECT id, job_url FROM job_listings WHERE job_description IS NULL")
    jobs = cursor.fetchall()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    for job_id, job_url in jobs:
        try:
            driver.get(job_url)
            wait = WebDriverWait(driver, 10)
            description_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='job-description']"))
            )
            job_description = description_element.text.strip()

            cursor.execute("""
                UPDATE job_listings
                SET job_description = %s
                WHERE id = %s
            """, (job_description, job_id))
            conn.commit()
            print(f"Updated job description for job ID {job_id}")

        except TimeoutException:
            print(f"Job description not found or timed out for job ID {job_id}")
        except Exception as e:
            print(f"Error for job ID {job_id}: {e}")

    driver.quit()


# Main workflow

def main():
    html_snippets = [
        # 1. Maroon
        {
            "html": """<div class="p-4">
<a class="content-center" href="/company/maroon-io">
<h2 class="inline text-md font-semibold">Maroon</h2></a>
<h4 class="styles-module_component__3ZI84 styles-module_flow__FV70c styles_jobTitle__01EmE text-lg font-medium">DeFi Data Analyst</h4>
<div class="mt-0.5 flex flex-col flex-wrap text-sm text-dark-aa md:flex-row">
<span class="md:truncate line-clamp-2 md:line-clamp-none" data-testid="location-display" data-truncate="true">Remote only • Everywhere</span>
<span class="styles_compensation__DUzmb">$35k – $40k • No equity</span>
</div>
<a class="styles-module_component__88XzG" href="/company/maroon-io/jobs">View 6 jobs</a></div>""",
            "source": "Maroon"
        },
        # 2. GoDaddy
        {
            "html": """<h2 class="inline text-md font-semibold">GoDaddy</h2>
<h4 class="styles-module_component__3ZI84 styles-module_flow__FV70c styles_jobTitle__01EmE text-lg font-medium">Marketing Data Analyst</h4>
<span class="md:truncate line-clamp-2 md:line-clamp-none" data-testid="location-display" data-truncate="true">Remote only • India</span>
<span class="styles_compensation__3JnvU">₹29,000 – ₹40,000</span>
<a class="styles-module_component__88XzG" href="/company/godaddy/jobs">View 6 jobs</a>""",
            "source": "GoDaddy"
        },
        # 3. Marvin
        {
            "html": """<h2 class="inline text-md font-semibold">Marvin</h2>
<h4 class="styles-module_component__3ZI84 styles-module_flow__FV70c styles_jobTitle__01EmE text-lg font-medium">Data analyst at Marvin (www.heymarvin.com) (Remote)</h4>
<span class="md:truncate line-clamp-2 md:line-clamp-none" data-testid="location-display" data-truncate="true">Remote only • India</span>
<span class="styles_compensation__DUzmb">₹12L – ₹16L • 0.0% – 0.02%</span>
<a class="styles-module_component__88XzG" href="/company/heymarvin/jobs">View 9 jobs</a>""",
            "source": "Marvin"
        },
        # 4. DoosriGaadi
        {
            "html": """<h2 class="inline text-md font-semibold">DoosriGaadi</h2>
<h4 class="styles-module_component__3ZI84 styles-module_flow__FV70c styles_jobTitle__01EmE text-lg font-medium">Data Analyst</h4>
<span class="md:truncate line-clamp-2 md:line-clamp-none" data-testid="location-display" data-truncate="true">Onsite or remote • Bengaluru • Mumbai • Remote (Everywhere)</span>
<span class="styles_compensation__DUzmb">₹4.75L – ₹13.45L</span>
<a class="styles-module_component__88XzG" href="/company/doosrigaadi/jobs">View 1 job</a>""",
            "source": "DoosriGaadi"
        }
    ]

    conn, cursor = connect_db()
    jobs_data = scrape_static_jobs(html_snippets)
    insert_jobs(cursor, conn, jobs_data)
    scrape_job_descriptions(cursor, conn)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
