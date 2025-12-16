# Weather Analysis Aktau (2018–2025)

Полный цикл: сбор → очистка → EDA → моделирование прогноза температуры.

## Структура
- `data/raw/` — сырые данные из скраппера (`weather_output.csv`).
- `data/processed/` — место для подготовленных датасетов.
- `notebooks/analysis.ipynb` — очистка, EDA, визуализации (6+ графиков), модели (3 базовых + тюнинг RF).
- `src/scrapper.py` — сбор данных с pogodaiklimat.ru (станция 38111), пишет в `data/raw/weather_output.csv`.
- `images/visualizations/` — сохраняйте графики для презентации/README.
- `presentation_outline.md` — шаблон слайдов под требования.
- `requirements.txt`, `.gitignore`, `README.md`.

## Запуск
1) Установить зависимости:
```bash
pip install -r requirements.txt
```
2) Собрать данные (по умолчанию год 2025):
```bash
python src/scrapper.py
```
Можно задать диапазон: `START_YEAR=2023 END_YEAR=2025 python src/scrapper.py`.
3) Открыть `notebooks/analysis.ipynb` и выполнить все ячейки.

## Модели
- Linear Regression (базовый бенчмарк)
- RandomForest Regressor
- GradientBoosting Regressor
- Тюнинг RF через GridSearchCV, метрики: MAE, RMSE, R². Важности признаков + анализ остатков.

## Визуализации
Линия (rolling temp), гистограмма температуры, роза ветров, heatmap корреляций, boxplot по месяцам, регрессия влажность–температура, plus feature importance и остатки.

## Презентация
Скелет слайдов в `presentation_outline.md`; экспортируйте в `presentation.pptx`/`pdf`, добавьте графики из `images/visualizations/`.

## Зависимости
См. `requirements.txt` (pandas, numpy, matplotlib, seaborn, scikit-learn, windrose, requests, beautifulsoup4).

