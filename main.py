from selenium import webdriver
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import csv


def get_id_list():
    # инициализация работы браузера
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    all_professions = []
    all_ids = set()
    driver.get(f'https://prodoctorov.ru/kazan/vrach/')
    page_source = driver.page_source
    bsobj = BeautifulSoup(page_source, 'lxml')
    # парсинг страницы, получение профессий докторов.

    button = driver.find_element(By.CLASS_NAME, "b-toggle-block__toggle-btn")
    button.click()

    data = bsobj.find_all('a', class_='p-doctors-list-page__tab-item-link b-text-unit_hover_solid ui-text ui-text_body-2')

    for element in data:
        all_professions.append(element['href'])

    # парсинг страниц профессий, получение id.

    for ref in all_professions:
        page_ids = []
        page_counter = 1
        driver.get(f'https://prodoctorov.ru{ref}')
        page_source = driver.page_source
        bsobj = BeautifulSoup(page_source, 'lxml')
        while True:
            page_counter += 1
            doctor_cards = bsobj.find_all('div', class_='b-doctor-card timetable_loaded')
            doctor_cards_2 = bsobj.find_all('div', class_='b-doctor-card')
            if doctor_cards or doctor_cards_2:
                if doctor_cards:
                    for card in doctor_cards:
                        page_ids.append(card['data-doctor-id'])
                if doctor_cards_2:
                    for card_2 in doctor_cards_2:
                        page_ids.append(card_2['data-doctor-id'])
                for elem in page_ids:
                    all_ids.add(elem)
                page_ids = []
                driver.get(f'https://prodoctorov.ru{ref}?page={page_counter}')
                page_source = driver.page_source
                bsobj = BeautifulSoup(page_source, 'lxml')
            else:
                break

    return all_ids


def get_table(id_list):
    # список на случай неизвестного айди
    error = []
    # основная таблица
    table = {}
    # инициализация работы браузера
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    for id in id_list:
        print(id)
        all_professions = set()
        m_r = []
        clinici = []
        adresses = []
        driver.get(f'https://prodoctorov.ru/kazan/vrach/{str(id)}')
        page_source = driver.page_source
        bs_obj = BeautifulSoup(page_source, 'lxml')

        # поиск ФИО

        fio = bs_obj.find('span', class_='d-block ui-text ui-text_h5 ui-text_color_black mb-2')
        if fio:
            fio = fio.get_text().strip()
        else:
            # на случай, если айди неизвестен(т.е по какой-то причине страница пуста)
            error.append(id)

        # формирование списка профессий врача

        profession_highlight = bs_obj.find_all('a', class_='b-doctor-intro__spec b-doctor-intro__spec_highlight')
        professions = bs_obj.find_all('a', class_='b-doctor-intro__spec')
        for prof in profession_highlight:
            all_professions.add(prof.get_text().strip())
        for prof2 in professions:
            all_professions.add(prof2.get_text().strip())

        # получение названия клиники и адреса работы

        adress_clinica = bs_obj.find_all('a', class_='b-doctor-contacts__lpu-name ui-text ui-text_subtitle-1')
        for clinica in adress_clinica:
            clinici.append(clinica.get_text())
        adress_adress = bs_obj.find_all('div', class_='b-doctor-contacts__lpu-address ui-text ui-text_subtitle-1')
        for adress in adress_adress:
            adresses.append(adress.get_text())
        for j in range(len(adress_adress)):
            one_adress = []
            if clinici[j]:
                one_adress.append(clinici[j])
            one_adress.append(adresses[j].strip())
            m_r.append(one_adress)

        # формирование списка цен(если указаны)

        price = bs_obj.find_all('div', class_='appointment-type-tab__inner')
        index = 0
        if price:
            for pr in price:
                text = pr.get_text().strip()
                text = " ".join(text.split())
                if '%' or 'онлайн' in text:
                    m_r[index].append(text)
                else:
                    m_r[index].append(text)
                    index += 1

        # получение количества отзывов

        reviews = bs_obj.find('a', href='#otzivi')
        if reviews:
            reviews = reviews.get_text()[6:]
            if len(reviews) == 0:
                reviews = 0
        else:
            reviews = '0'

        # получение рейтинга

        rate = bs_obj.find('div', class_='ui-text ui-text_h5 ui-text_color_black font-weight-medium mr-2')
        if rate:
            rate = rate.get_text().strip()

        # получение стажа

        years = bs_obj.find('div', class_='ui-text ui-text_subtitle-2')
        if years:
            years = years.get_text().strip()

        # получение категории

        category = bs_obj.find('div', class_='ui-text ui-text_body-2 mt-1')
        if category:
            category = category.get_text()
        if not category:
            category = 'н/у'

        # приведение данных в читабельный вид

        profs = []
        for prof in all_professions:
            profs.append(prof)
        all_professions = ', '.join(profs)

        m_r_table = []
        for w_p in m_r:
            st = w_p[0] + ' ' + w_p[1]
            if len(w_p) == 3:
                st += f'({w_p[2]})'
            elif len(w_p) == 4:
                st += f'({w_p[2]}, {w_p[3]})'
            m_r_table.append(st)
        m_r = ', '.join(m_r_table)

        # формирование строки итоговой таблицы

        table[id] = {'фио': fio, 'специальность': all_professions, 'место работы': m_r, 'отзывы': reviews,
                     'рейтинг': rate, 'стаж': years, 'категория': category}
        # print(table[id])

        # укладываем парсер спать, чтобы злой антиробот ничего не заподозрил
        time.sleep(1.2)
    return table


def form_csv(table, file):
    with open(file, 'w', newline='', encoding='utf-16') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        print(table)
        writer.writerow(('ФИО', 'специальность', 'место работы', 'отзывы', 'рейтинг', 'стаж', 'категория'))
        writer.writerows((table[id]['фио'], table[id]['специальность'], table[id]['место работы'], table[id]['отзывы'],
                          table[id]['рейтинг'], table[id]['стаж'], table[id]['категория']) for id in table.keys())


ids = get_id_list()
t = get_table(ids)
form_csv(t, 'all.csv')