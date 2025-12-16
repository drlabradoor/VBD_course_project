import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import csv
import calendar
import time
import json
import re
import os
from pathlib import Path

#region agent log
LOG_PATH = Path(r"d:\_work\project\.cursor\debug.log")


def agent_log(hypothesis_id: str, location: str, message: str, data=None, run_id: str = "pre-fix"):
    payload = {
        "sessionId": "debug-session",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
#endregion

# network session with retries and UA to be a kinder client
SESSION = requests.Session()
SESSION.headers.update(
    {"User-Agent": "aktn-weather-scraper/1.0 (+https://example.com; student project)"}
)
SESSION.mount(
    "http://",
    HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])),
)
SESSION.mount(
    "https://",
    HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])),
)

def scrape_weather_data(month: int, year: int):
    #region agent log
    agent_log("A", "scrapper.py:scrape_weather_data", "start scrape", {"month": month, "year": year})
    #endregion
    # Вычисляем последний день месяца
    last_day = calendar.monthrange(year, month)[1]
    # Формируем URL по шаблону
    url = f"http://www.pogodaiklimat.ru/weather.php?id=38111&bday=1&fday={last_day}&amonth={month}&ayear={year}&bot=2"
    print(f"Fetching data from: {url}")
    
    response = SESSION.get(url, timeout=30)
    response.encoding = 'utf-8'
    if response.status_code != 200:
        raise Exception(f"Не удалось получить данные с сайта за {month}/{year}.")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Находим основной блок таблицы
    archive_div = soup.find("div", class_="archive-table")
    if not archive_div:
        raise Exception("Блок 'archive-table' не найден.")
    
    # Левый блок с датой и временем
    left_div = archive_div.find("div", class_="archive-table-left-column")
    # Правый блок с основной информацией
    right_div = archive_div.find("div", class_="archive-table-wrap")
    if not left_div or not right_div:
        raise Exception("Не найдены обе части таблицы (left-column и wrap).")
    
    # Извлекаем строки левой таблицы
    left_table = left_div.find("table")
    if not left_table:
        raise Exception("Таблица в левой колонке не найдена.")
    left_rows = []
    for tr in left_table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        row = [cell.get_text(strip=True) for cell in cells]
        if row:
            left_rows.append(row)
    # исправляем слитый заголовок "Время(UTC), дата" в одну ячейку
    if left_rows and len(left_rows[0]) == 1 and "Время" in left_rows[0][0] and "дата" in left_rows[0][0]:
        left_rows[0] = ["Время(UTC)", "Дата"]
    
    # Извлекаем строки правой таблицы
    right_table = right_div.find("table")
    if not right_table:
        raise Exception("Таблица в правой колонке не найдена.")
    right_rows = []
    for tr in right_table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        row = [cell.get_text(strip=True) for cell in cells]
        if row:
            right_rows.append(row)
    
    if len(left_rows) != len(right_rows):
        print("Предупреждение: количество строк в левой и правой колонках не совпадает.")
        #region agent log
        agent_log("A", "scrapper.py:scrape_weather_data", "row count mismatch", {"left_rows": len(left_rows), "right_rows": len(right_rows)})
        #endregion
    
    # Объединяем строки: для каждой строки из левой части добавляем соответствующую строку из правой части.
    combined_rows = []
    date_pattern = re.compile(r"^\d{1,2}\.\d{2}$")
    for left, right in zip(left_rows, right_rows):
        row = left + right
        # enrich date with year when it looks like DD.MM
        if len(row) > 1 and date_pattern.match(str(row[1])):
            row[1] = f"{row[1]}.{year}"
        combined_rows.append(row)

    #region agent log
    agent_log("A", "scrapper.py:scrape_weather_data", "scrape complete", {"month": month, "year": year, "rows": len(combined_rows)})
    #endregion
    
    return combined_rows

def main():
    start_year = int(os.getenv("START_YEAR", 2025))
    end_year = int(os.getenv("END_YEAR", start_year))

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "weather_output.csv"
    first_write = True

    for year in range(start_year, end_year + 1):
        for month in range(1, 12 + 1):
            print(f"\nСбор данных за {month}/{year}...")
            try:
                data = scrape_weather_data(month, year)
            except Exception as e:
                print(f"Ошибка за {month}/{year}: {e}")
                #region agent log
                agent_log("B", "scrapper.py:main", "scrape failed", {"month": month, "year": year, "error": str(e)})
                #endregion
                continue

            mode = "w" if first_write else "a"
            with open(output_file, mode, encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f, delimiter=",")  # <-- CSV формат
                if first_write:
                    writer.writerows(data)
                    first_write = False
                else:
                    writer.writerows(data[1:])
            #region agent log
            agent_log("C", "scrapper.py:main", "write complete", {"month": month, "year": year, "rows_written": len(data)})
            #endregion
            # Небольшая задержка между запросами, чтобы не перегружать сервер
            time.sleep(1)
    
    print(f"\nДанные собраны и сохранены в файле {output_file}")

if __name__ == "__main__":
    main()
