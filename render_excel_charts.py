"""Exports the workbook's Excel charts as PNG images for the README (needs LibreOffice)."""
from xlkit.charts import render

PAGES = {"Overview": "overview.png", "Chart AR vs EN": "arabic_vs_english.png", "Parity": "parity_heatmap.png",
         "Chart Languages": "languages_ranking.png", "Chart Vocab vs Tax": "vocab_vs_tax.png", "Chart Region": "region_radar.png",
         "Chart Words": "tokens_per_word.png", "Chart Over Time": "over_time.png", "Chart Vocab Scripts": "vocab_scripts.png",
         "Chart Tekken Donut": "tekken_donut.png", "Chart Digits": "digits.png", "Chart Dialect": "dialect.png", "Chart Cost": "extra_cost.png"}
for n in render("excel/arabic_token_tax.xlsx", PAGES, "results"):
    print(n, "->", PAGES[n])
