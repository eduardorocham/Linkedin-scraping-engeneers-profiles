import random
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from time import sleep
import pandas as pd

# 1 Open Chrome and Access Linkedin login site
browser = webdriver.Chrome()
browser.get('https://www.linkedin.com/login')
print("Navegador inicializado")
sleep(random.randint(2, 5))

# 1.1 Get Login Credentials
credential = open('credentials.txt')
line = credential.readlines()
email = line[0]
password = line[1]

# 1.2 Get Auth fields
email_field = browser.find_element(By.ID, 'username')
password_field = browser.find_element(By.NAME, 'session_password')

# 1.3 Do login
email_field.send_keys(email)
password_field.send_keys(password)
sleep(random.randint(2, 5))
password_field.submit()
sleep(random.randint(2, 5))
print("Login realizado com sucesso")

# 2 Search for the profile we want to crawl
encoded_company = '%5B%224120%22%5D'
encoded_locality = '%5B%22103658898%22%5D'
browser.get(f'https://www.linkedin.com/search/results/people/?currentCompany={encoded_company}&geoUrn={encoded_locality}&keywords=engenheiro%20civil&sid=N4D')
print("Busca por perfis rezalizada com sucesso")
sleep(20)

# # 2.1 Locate the search bar element
# search_field = browser.find_element(By.CLASS_NAME, 'search-global-typeahead__input')

# # 2.2: Input the search query to the search bar
# search_field.send_keys('engenheiro civil')
# sleep(random.randint(2, 5))

# # 2.3: Search
# search_field.send_keys(Keys.RETURN)
# sleep(random.randint(4, 7))

# 2.4 Search by profile
# profiles_button = browser.find_element(By.XPATH, '//ul/li[button[text()="Pessoas"]]')
# profiles_button.click()

# 3 Scrape the URLs of the profiles

# 3.1 Function to extract the URLs of one page
def GetUrl():
    page_content = browser.page_source
    current_page = BeautifulSoup(page_content)

    # 3.1.1 Get profiles divs
    profiles_divs = current_page.find_all('div', attrs={'class': 'entity-result'})
    # 3.1.2 Get 'a' tags from profile divs
    a_tags = []
    for div in profiles_divs:
        a_tag = div.find('a', attrs={'class': 'app-aware-link'})
        a_tags.append(a_tag)
    # 3.1.3 Get urls from 'a' tags
    all_profile_URL = []
    for each_a_tag in a_tags: # Imprime a tag <a> completa
        profile_URL = each_a_tag['href']
        if profile_URL not in all_profile_URL:
            all_profile_URL.append(profile_URL)
    return all_profile_URL

# 3.2 Navigate through many page, and extract the profile URLs of each page
number_of_pages = 1
URLs_all_page = []
for page in range(number_of_pages):
    URLs_one_page = GetUrl()
    sleep(random.randint(2, 5))
    browser.execute_script('window.scrollTo(0, document.body.scrollHeight);') #scroll to the end of the page
    sleep(random.randint(2, 5))
    next_button = browser.find_element(By.CLASS_NAME, "artdeco-pagination__button--next")
    browser.execute_script("arguments[0].click();", next_button)
    URLs_all_page = URLs_all_page + URLs_one_page
    sleep(random.randint(2, 5))

print("Todas as URLS dos perfis foram obtidas")

# 4 Scrape the data of 1 Linkedin profile, and write the data to a .CSV file
list_data_profiles = []
for linkedin_URL in URLs_all_page:
    data_one_profile = []
    browser.get(linkedin_URL)
    print()
    print('Acessando perfil: ', linkedin_URL)
    sleep(random.randint(2, 5))

    profile_page = BeautifulSoup(browser.page_source, "html.parser")

    # name
    name = profile_page.find('h1', attrs={'class', 'text-heading-xlarge inline t-24 v-align-middle break-words'})
    if name is None:
        print('Não foi possível acessar a url do perfil')
        continue
    data_one_profile.append(name.text)

    # contact
    contact_button = browser.find_element(By.ID, 'top-card-text-details-contact-info')
    contact_button.click()
    sleep(random.randint(4, 7))
    data_contact_modal = BeautifulSoup(browser.page_source, "html.parser")
    data_contact_sections = data_contact_modal.find_all('section', attrs={'class': 'pv-contact-info__contact-type'})
    all_data_contact = []
    for data_contact_element in data_contact_sections:
        title = data_contact_element.find('h3').text.strip()

        content = []

        div_info = data_contact_element.find('div', attrs={'class': 'pv-contact-info__ci-container'})
        if div_info is not None:
            contact_link = div_info.find('a')
            if contact_link is not None:
                contact_href = contact_link.get('href').strip()
                if contact_href is not None:
                    content.append(contact_href)
            else:
                data_span = div_info.find('span').text.strip()
                content.append(data_span)

        ul_infos = data_contact_element.find('ul')
        if (ul_infos is not None):
            links_contact_list = ul_infos.find_all('li')
            for li in links_contact_list:
               contact_link = li.find('a')['href']
               content.append(contact_link)
        content_string = ", ".join(content)
        data_string = ": ".join([title, content_string])
        all_data_contact.append(data_string)
    data_one_profile.append("| ".join(all_data_contact))
    browser.back()
    sleep(random.randint(4, 7))

    # about
    div_about_element = profile_page.find('div', attrs={'id': 'about'})
    if div_about_element:
        section_about_element = div_about_element.find_parent('section')
        about_span = section_about_element.find_all('span', attrs={'aria-hidden': 'true'})
        about_span_text = about_span[1].text.strip()
        data_one_profile.append(about_span_text)
    else:
        data_one_profile.append(' ')

    # experiences
    experiences = []
    div_experience = profile_page.find('div', attrs={'id': 'experience'})
    if div_experience:
        section_experience = div_experience.find_parent('section')
        experience_list = section_experience.find_all('div', attrs={'class': 'pvs-list__item--no-padding-in-columns'})
        if experience_list:
            print(len(experience_list))
            for experience_list_item in experience_list:
                div_title = experience_list_item.find('div', class_='display-flex flex-wrap align-items-center full-height')
                title = div_title.find('span', attrs={'aria-hidden': 'true'}).text
                print("Experiências de uma empresa:")
                print(title)
                has_more_one_office = experience_list_item.find_all('span', attrs={'class': 'pvs-entity__path-node'})
                if has_more_one_office:
                    print("Tem mais de um cargo")
                    offices = []
                    for one_office in has_more_one_office:
                        div_sibling = one_office.find_next_sibling('div')
                        office = div_sibling.find('span', attrs={'aria-hidden': 'true'})
                        offices.append(office.text)
                    all_offices = ", ".join(offices)
                    experiences.append(f'{title} - {all_offices}')
                else:
                    try:
                        secondary_title_span = experience_list_item.find('span', attrs={'class': 't-14 t-normal'})
                        secondary_title = secondary_title_span.find('span', attrs={'aria-hidden': 'true'}).text
                        experiences.append(f'{title} - {secondary_title}')
                        print(secondary_title)
                    except AttributeError:
                        continue
            experience_string = "| ".join(experiences)
            data_one_profile.append(experience_string)
    else:
        print("Experiência não encontrada")
        data_one_profile.append(' ')

    # formations
    try:
        formations_list = []
        see_all_education_button = browser.find_element(By.ID, 'navigation-index-see-all-education')
        print('Botão de ver todas a formações encontrado')
        see_all_education_button.click()
        sleep(random.randint(4, 7))
        education_page = BeautifulSoup(browser.page_source,"html.parser")
        formations_list = education_page.find_all('div', attrs={'class': 'pvs-entity'})
        formations_list = section_education.find_all('div', attrs={'class': 'pvs-entity'})
        # formations = []
        # for formation_list_item in formations_list:
        #     institution = formation_list_item.find('span', attrs={'aria-hidden': 'true'})
        #     level_span = formation_list_item.find('span', attrs={'class': 't-14 t-normal'})
        #     if (level_span is not None):
        #         level = level_span.find('span', attrs={'aria-hidden': 'true'})
        #         formations.append(institution.text + ' ' + '-' + ' ' + level.text)
        #     else:
        #         formations.append(institution.text)
        # formations_string = "| ".join(formations)
        # data_one_profile.append(formations_string)
        browser.back()
    except NoSuchElementException:
        print('Botão de ver todas a formações não encontrado')
        div_education = profile_page.find('div', {'id': 'education'})
        if div_education:
            section_education = div_education.find_parent('section')
            formations_list = section_education.find_all('div', attrs={'class': 'pvs-entity'})
    formations = []
    if len(formations_list) > 0:
        for formation_list_item in formations_list:
            institution = formation_list_item.find('span', attrs={'aria-hidden': 'true'})
            level_span = formation_list_item.find('span', attrs={'class': 't-14 t-normal'})
            if (level_span is not None):
                level = level_span.find('span', attrs={'aria-hidden': 'true'})
                formations.append(institution.text + ' ' + '-' + ' ' + level.text)
            else:
                formations.append(institution.text)
        formations_string = "| ".join(formations)
        data_one_profile.append(formations_string)
    else:
        data_one_profile.append(' ')

    # certifications
    try:
        see_all_certifications_button = browser.find_element(By.ID, 'navigation-index-see-all-licenses-and-certifications')
        print('Botão de ver todas a certificações encontrado')
        see_all_certifications_button.click()
        sleep(random.randint(4, 7))
        certifications_page = BeautifulSoup(browser.page_source,"html.parser")
        certifications_list = certifications_page.find_all('div', attrs={'class': 'pvs-entity'})
        browser.back()
    except NoSuchElementException:
        print('Botão de ver todas a certificações não encontrado')
        div_certifications = profile_page.find('div', {'id': 'licenses_and_certifications'})
        if (div_certifications):
            section_certifications = div_certifications.find_parent('section')
            certifications_list = section_certifications.find_all('div', attrs={'class': 'pvs-entity'})
        else:
            certifications_list = []
    certifications = []
    for certification_list_item in certifications_list:
        certification_name = certification_list_item.find('span', attrs={'aria-hidden': 'true'})
        entity_span = certification_list_item.find('span', attrs={'class': 't-14 t-normal'})
        entity = entity_span.find('span', attrs={'aria-hidden': 'true'})
        certifications.append(certification_name.text + ' ' + '-' + ' ' + entity.text)
    if (len(certifications) > 0):
        certifications_string = "| ".join(certifications)
        data_one_profile.append(certifications_string)
    else:
        data_one_profile.append(' ')

    #skills
    sleep(random.randint(4, 7))
    try:
        div_skills = browser.find_element(By.ID, 'skills')
        section_skills = div_skills.find_element(By.XPATH, './ancestor::section')
        try:
            button_see_all_skills = section_skills.find_element(By.CLASS_NAME, 'pvs-navigation__text')
            button_see_all_skills.click()
            sleep(random.randint(4, 7))
            skills_page = BeautifulSoup(browser.page_source,"html.parser")
            skills_list = skills_page.find_all('div', attrs={'class': 'pvs-entity'})
        except:
            print('Não há botão ver mais competências')
            skills_list = section_skills.find_all('div', attrs={'class': 'pvs-entity'})
    except:
        print('Div skills não encontrada')
        skills_list = []
    skills = []
    for skills_list_item in skills_list:
        skill = skills_list_item.find('span', attrs={'aria-hidden': 'true'})
        skill_text = skill.text.strip()
        if skill_text not in skills:
            skills.append(skill_text)
    if (len(skills) > 0):
        skills_string = "| ".join(skills)
        data_one_profile.append(skills_string)
    else:
        data_one_profile.append(' ')

    list_data_profiles.append(data_one_profile)
    browser.execute_script('window.scrollTo(0, document.body.scrollHeight);') #scroll to the end of the page

# 5 Write the data to a .xlsx file
data_profiles = pd.DataFrame(list_data_profiles, columns=[
    'Nome', 'Contato', 'Sobre', 'Experiência', 'Formação Acadêmica', 'Certificações', 'Competências'
])

data_profiles.to_excel('dados.xlsx', index=False)
print("Arquivo xlsx criado com sucesso")