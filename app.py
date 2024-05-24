import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from chromedriver_py import binary_path
import time
import os
from dotenv import load_dotenv

load_dotenv()

svc = webdriver.ChromeService(executable_path=binary_path)
driver = webdriver.Chrome(service=svc)
driver.maximize_window()

is_logged_in = False


def login():
    # Open the Python website
    driver.get("https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin")

    time.sleep(4)

    username = driver.find_element(By.XPATH, "//input[@name='session_key']")
    password = driver.find_element(By.XPATH, "//input[@name='session_password']")

    username.send_keys(os.getenv("LINKEDIN_LOGIN"))
    password.send_keys(os.getenv("LINKEDIN_PASSWORD"))

    time.sleep(2)

    submit = driver.find_element(By.XPATH, "//button[@type='submit']")
    submit.click()
    is_logged_in = True
    time.sleep(2)


def linkedin_jobs_to_csv():

    if not is_logged_in:
        login()

    driver.get(f"https://www.linkedin.com/jobs/search/?keywords={os.getenv('JOB_TITLE')}&location={os.getenv('JOB_LOCATION')}&sortBy=DD")

    time.sleep(3)

    links = []
    print('Links are being collected now.')

    try:
        for page in range(2, 3):
            time.sleep(2)
            jobs_list = driver.find_elements(By.CSS_SELECTOR, 'ul.scaffold-layout__list-container > li')

            for job in jobs_list:
                all_links = job.find_elements(By.CSS_SELECTOR, 'a')
                for a in all_links:
                    if str(a.get_attribute('href')).startswith(
                            "https://www.linkedin.com/jobs/view") and a.get_attribute(
                            'href') not in links:
                        links.append(a.get_attribute('href'))
                    else:
                        pass
                # scroll down for each job element
                driver.execute_script("arguments[0].scrollIntoView();", job)

            print(f'Collecting the links in the page: {page - 1}')
            # go to next page:
            driver.find_element(By.XPATH, f"//button[@aria-label='Page {page}']").click()
            time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        pass
    print('Found ' + str(len(links)) + ' links for job offers')

    # Create empty lists to store information
    job_titles = []
    company_names = []
    company_locations = []
    work_methods = []
    post_dates = []
    job_desc = []

    i = 0
    j = 1
    # Visit each link one by one to scrape the information
    print('Visiting the links and collecting information just started.')
    for i in range(len(links)):
        try:
            driver.get(links[i])
            i = i + 1
            time.sleep(2)
            # Click See more.
            driver.find_element(By.CSS_SELECTOR, "button.artdeco-card__action").click()
            time.sleep(1)
        except:
            pass

        # Find the general information of the job offers
        contents = driver.find_elements(By.CSS_SELECTOR, 'div.p5 > div')
        for content in contents:
            try:
                job_titles.append(content.find_element(By.CSS_SELECTOR, "h1").text)
                company_names.append(
                    driver.find_element(By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__company-name a').text)
                company_locations.append(driver.find_element(By.CSS_SELECTOR,
                                                             'div.job-details-jobs-unified-top-card__tertiary-description span:nth-child(1)').text)

                # Find all elements containing the working methods information
                working_methods_elements = driver.find_elements(By.CSS_SELECTOR,
                                                                'span.ui-label.ui-label--accent-3.text-body-small')
                # Extract the text content from each element
                working_method = [element.text[:element.text.index("\n")] for element in working_methods_elements]
                work_methods.append(working_method)
                post_dates.append(driver.find_element(By.CSS_SELECTOR,
                                                      'div.job-details-jobs-unified-top-card__tertiary-description span:nth-child(3)').text)
                # work_times.append(content.find_element_by_class_name("jobs-unified-top-card__job-insight").text)
                print(len(job_titles), len(company_names), len(company_locations))
                j += 1
            except:
                pass

            # Scraping the job description
        job_description = driver.find_elements(By.CSS_SELECTOR, 'div.jobs-description__content')
        for description in job_description:
            job_text = description.find_element(By.CSS_SELECTOR, "div.jobs-box__html-content").text + '\n'
            job_desc.append(job_text)
            print(f'Scraping the Job Offer {j}')

    # Creating the dataframe
    datamap = {'job_title': job_titles, 'company_name': company_names, 'company_location': company_locations,
               'job_types': work_methods, 'job_desc': job_desc}

    # Verify DataFrame creation
    df = pd.DataFrame(datamap)
    print(df)  # Print the DataFrame head to check if it's created correctly

    # Storing the data to csv file
    df.to_csv('job_offers.csv', index=False)


def perform_analysis():
    jobs = pd.read_csv('job_offers.csv')


def fill_the_form():
    fields = driver.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-section__grouping")

    resume_data = {
        "phone": os.getenv("CONTACT_PHONE"),
        "experience": os.getenv("EXPERIENCE_IN_YEARS"),
        "email": os.getenv("CONTACT_EMAIL"),
        #"authorization": os.getenv("ARE_YOU_AUTHORIZED"),
        #"sponsorship": os.getenv("WILL_YOU_EVER_REQUIRE_SPONSORSHIP")
    }

    for field in fields:
        if "phone" in field.text:
            field_input = field.find_element(By.TAG_NAME, "input")
            field_input.clear()
            field_input.send_keys(resume_data["phone"])
        elif "email" in field.text:
            field_input = field.find_element(By.TAG_NAME, "input")
            field_input.clear()
            field_input.send_keys(resume_data["email"])


def apply(job_url):

    if not is_logged_in:
        login()

    driver.get(job_url)

    easy_apply_button = driver.find_element(By.XPATH, '//button[contains(text(), "Easy Apply")]')
    easy_apply_button.click()
    time.sleep(2)

    fill_the_form()

    submit_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
    submit_button.click()


def start_applying(jobs):
    for job in jobs:
        apply(job.url)


def quite_the_app():
    driver.quit()


if __name__ == '__main__':
    if not is_logged_in:
        login()

