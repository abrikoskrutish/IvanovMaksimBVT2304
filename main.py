import requests
import psycopg2
from pywebio import input, output, start_server



DATABASE = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '1',
    'host': 'localhost',
    'port': '5432'
}

def clear_vacancies_table():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM vacancies")
        cur.execute("ALTER SEQUENCE vacancies_id_seq RESTART WITH 1")
        conn.commit()
    except Exception as e:
        print(f"Ошибка при очистке: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def connect_db():
    conn = psycopg2.connect(**DATABASE)
    return conn

def insert_vacancy(vacancy):
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO vacancies (hh_id, name, url, company, experience, salary)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            vacancy['id'],
            vacancy['name'],
            vacancy['url'],
            vacancy['company'],
            vacancy['experience'],
            vacancy['salary']
        ))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при добавлении вакансии: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def Vacancies(keyword, city):
    clear_vacancies_table()
    url = "https://api.hh.ru/vacancies"
    headers = {
        "User-Agent": "Your User Agent",
    }
    vacancies = []


    for page in range(200):
        params = {
            "text": keyword,
            "area": city,  # (1 is Moscow)
            "page": page,
            "per_page": 100,
        }

        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            if response.status_code == 400:
                break
            continue

        data = response.json()
        items = data.get("items", [])
        for item in items:

            salary_data = item.get("salary") or {}
            from_salary = salary_data.get("from")
            to_salary = salary_data.get("to")
            curr_salary = salary_data.get("currency")
            if from_salary and to_salary and curr_salary:
                salary = f"от {from_salary or ''} до {to_salary or ''} {curr_salary or ''}"
            elif from_salary and curr_salary:
                salary = f"от {from_salary or ''} {curr_salary or ''}"
            elif to_salary and curr_salary:
                salary = f"до {to_salary} {curr_salary or ''}"
            else:
                salary = "Не указана"
            output.put_text(f"ID: {item.get("id")}")
            output.put_text(f"Вакансия: {item.get("name")}")
            output.put_text(f"Комапания: {item.get("employer", {}).get("name")}")
            output.put_text(f"Ссылка: {item.get("alternate_url")}")
            output.put_text(f"Зарплата: {salary}")
            output.put_text("------------------")
            output.put_text("")

            vacancy_data = {
                "id": item.get("id"),
                "name": item.get("name"),
                "url": item.get("alternate_url"),
                "company": item.get("employer", {}).get("name"),
                "experience": item.get("experience", {}).get("name"),
                "salary": salary
            }

            insert_vacancy(vacancy_data)
            vacancies.append(vacancy_data)

        if page >= data.get('pages', 0) - 1:
            break

    return vacancies


def search_vacancies():
    keyword = input.input("название вакансии", type=input.TEXT)
    city = int(input.input("город", type=input.NUMBER))
    output.clear()
    output.put_text("Searching for vacancies...")
    Vacancies(keyword, city)


if __name__ == '__main__':
    start_server(search_vacancies, port=8080)