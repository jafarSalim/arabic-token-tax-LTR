"""Builds excel/arabic_token_tax.xlsx from results/measurements.json, with formulas and native Excel charts."""
import json, pathlib
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import BarChart, LineChart, ScatterChart, RadarChart, DoughnutChart, Reference, Series
from openpyxl.chart.series import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.trendline import Trendline
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter as L
from xlkit.charts import BLUE_IN, NOTE, OFFICE, header, style, fill, labels, chart_sheet, tiles, render

R = json.load(open("results/measurements.json", encoding="utf8"))
TOK = [t["name"] for t in R["tokenizers"]]
LANG = R["languages"]
wb = Workbook()
wb.remove(wb.active)
thin = Side(style="thin", color="BFBFBF")

# ---- Tokens (measured) ----
tk = wb.create_sheet("Tokens")
header(tk, 1, ["Language", "Characters", "UTF-8 bytes", "Words"] + TOK, [18, 11, 11, 9] + [12] * len(TOK))
for i, l in enumerate(LANG, 2):
    tk.cell(i, 1, l)
    tk.cell(i, 2, R["chars"][l]); tk.cell(i, 3, R["bytes"][l]); tk.cell(i, 4, R["words"][l])
    for j, t in enumerate(TOK, 5):
        tk.cell(i, j, R["tokens"][l][t]).number_format = "#,##0"
NL = len(LANG) + 1
tk.cell(NL + 2, 1, "Measured by tax/measure.py: the full Universal Declaration of Human Rights in each language (NLTK udhr2), normalized to Unicode NFC.").font = NOTE
tk.freeze_panes = "B2"

# ---- Parity (formulas) ----
pa = wb.create_sheet("Parity")
pa["A1"] = "Token tax: tokens for the same text ÷ tokens in English"
pa["A1"].font = Font(name="Calibri", bold=True, size=16, color="1F4E79")
pa["A2"] = "1.00 = same as English. 1.34 = 34% more tokens. Green is cheaper, red is more expensive."
pa["A2"].font = NOTE
header(pa, 4, ["Language"] + TOK, [18] + [12] * len(TOK))
for i, l in enumerate(LANG, 5):
    pa.cell(i, 1, l).font = Font(name="Calibri", bold=l in ("Arabic", "Kurdish (Sorani)"))
    for j in range(len(TOK)):
        c = pa.cell(i, 2 + j, f"=Tokens!{L(5 + j)}{i - 3}/Tokens!{L(5 + j)}$2")
        c.number_format, c.alignment, c.border = "0.00", Alignment(horizontal="center"), Border(thin, thin, thin, thin)
end = 4 + len(LANG)
pa.conditional_formatting.add(f"B5:{L(1 + len(TOK))}{end}", ColorScaleRule(start_type="num", start_value=1, start_color="63BE7B", mid_type="num", mid_value=1.6, mid_color="FFEB84", end_type="num", end_value=3, end_color="F8696B"))
pa.page_setup.orientation = "portrait"
pa.sheet_properties.pageSetUpPr.fitToPage = True
pa.print_area = f"A1:{L(1 + len(TOK))}{end}"
ROW = {l: 5 + i for i, l in enumerate(LANG)}
COL = {t: L(2 + j) for j, t in enumerate(TOK)}

# ---- Per tokenizer facts ----
ft = wb.create_sheet("Tokenizer Data")
header(ft, 1, ["Tokenizer", "Year", "Vocabulary", "Arabic share of vocab", "Arabic ÷ English", "Arabic tokens per word", "English tokens per word",
               "Arabic tokens", "English tokens", "Western digits", "Eastern digits"], [22, 7, 12, 14, 12, 13, 13, 12, 12, 12, 12])
for i, t in enumerate(R["tokenizers"], 2):
    n = t["name"]
    ft.cell(i, 1, n); ft.cell(i, 2, t["year"]); ft.cell(i, 3, t["vocab"]).number_format = "#,##0"
    ft.cell(i, 4, R["arabic_vocab_share"][n]).number_format = "0.0%"
    ft.cell(i, 5, f"=Parity!{COL[n]}{ROW['Arabic']}").number_format = "0.00"
    ft.cell(i, 6, f"=Tokens!{L(5 + TOK.index(n))}{LANG.index('Arabic') + 2}/Tokens!D{LANG.index('Arabic') + 2}").number_format = "0.00"
    ft.cell(i, 7, f"=Tokens!{L(5 + TOK.index(n))}2/Tokens!D2").number_format = "0.00"
    ft.cell(i, 8, f"=Tokens!{L(5 + TOK.index(n))}{LANG.index('Arabic') + 2}").number_format = "#,##0"
    ft.cell(i, 9, f"=Tokens!{L(5 + TOK.index(n))}2").number_format = "#,##0"
    ft.cell(i, 10, R["digits"][n]["western"]); ft.cell(i, 11, R["digits"][n]["eastern"])
NT = len(TOK) + 1
ft.cell(NT + 2, 1, f"Digits test: '{R['digits_text']['western']}' against the same numbers in Eastern Arabic digits.").font = NOTE
ft.cell(NT + 3, 1, "Arabic share of vocab: tokens whose text contains an Arabic-script character.").font = NOTE

# ---- Sorted languages on Llama 4 ----
so = wb.create_sheet("Ranking Data")
header(so, 1, ["Language", "Llama 4", "Mistral Tekken"], [18, 10, 14])
order = sorted(LANG, key=lambda l: R["parity"][l]["Llama 4"])
for i, l in enumerate(order, 2):
    so.cell(i, 1, l)
    so.cell(i, 2, f"=Parity!{COL['Llama 4']}{ROW[l]}").number_format = "0.00"
    so.cell(i, 3, f"=Parity!{COL['Mistral Tekken']}{ROW[l]}").number_format = "0.00"

# ---- Fertility histogram ----
fh = wb.create_sheet("Words Data")
header(fh, 1, ["Tokens per word", "Arabic", "English"], [16, 10, 10])
for k in range(1, 7):
    fh.cell(k + 1, 1, f"{k}+" if k == 6 else str(k))
    fh.cell(k + 1, 2, R["fertility_hist"]["Arabic"]["Llama 4"][str(k)]).number_format = "0%"
    fh.cell(k + 1, 3, R["fertility_hist"]["English"]["Llama 4"][str(k)]).number_format = "0%"

# ---- Scripts in vocab ----
sc = wb.create_sheet("Scripts Data")
scripts = list(R["vocab_scripts"]["Llama 4"])
header(sc, 1, ["Tokenizer"] + scripts, [22] + [12] * len(scripts))
for i, n in enumerate(TOK, 2):
    sc.cell(i, 1, n)
    for j, s in enumerate(scripts, 2):
        sc.cell(i, j, R["vocab_scripts"][n][s]).number_format = "0.0%"

# ---- Dialect ----
di = wb.create_sheet("Dialect Data")
header(di, 1, ["Tokenizer", "English", "Modern Standard Arabic", "Iraqi Arabic"], [22, 10, 14, 12])
for i, n in enumerate(TOK, 2):
    di.cell(i, 1, n)
    for j, k in enumerate(("english", "msa", "iraqi"), 2):
        di.cell(i, j, R["dialect"][k][n])
di.cell(NT + 2, 1, f"{R['dialect_sentences']} everyday sentences written for this project in three versions. See data_samples/dialect_sample.json.").font = NOTE

# ---- Cost calculator ----
cc = wb.create_sheet("Cost Calculator", 0)
cc.column_dimensions["A"].width, cc.column_dimensions["B"].width, cc.column_dimensions["C"].width = 40, 16, 18
cc["A1"] = "What the Arabic token tax costs you"
cc["A1"].font = Font(name="Calibri", bold=True, size=16, color="1F4E79")
cc["A3"], cc["B3"] = "Content per month, measured in English tokens", 100_000_000
cc["A4"], cc["B4"] = "Price, USD per million input tokens", 2
cc["A5"] = "Example: $2 is Claude Sonnet 5.5 input (platform.claude.com pricing, Nov 2026). Claude's tokenizer is not public, so its tax is not measured here."
cc["A5"].font = NOTE
for c in ("B3", "B4"):
    cc[c].font = BLUE_IN
cc["B3"].number_format, cc["B4"].number_format = "#,##0", '"$"0.00'
header(cc, 7, ["Tokenizer", "Arabic ÷ English", "Extra USD per month"])
for i, n in enumerate(TOK, 8):
    cc.cell(i, 1, n)
    cc.cell(i, 2, f"=Parity!{COL[n]}{ROW['Arabic']}").number_format = "0.00"
    cc.cell(i, 3, f"=$B$3*(B{i}-1)*$B$4/1000000").number_format = '"$"#,##0'

# ================= Charts =================
c1 = BarChart(); c1.type = "col"; c1.gapWidth = 60
for col, colr in ((9, "4472C4"), (8, "ED7D31")):
    s = Series(Reference(ft, min_col=col, min_row=1, max_row=NT), title_from_data=True)
    fill(s, colr); labels(s, "#,##0", "outEnd"); c1.series.append(s)
c1.set_categories(Reference(ft, min_col=1, min_row=2, max_row=NT))
c1.y_axis.title = "Tokens for the whole document"; c1.y_axis.numFmt = "#,##0"; c1.legend.position = "b"
style(c1, "Same document, English vs Arabic: tokens on 7 tokenizers")
chart_sheet(wb, "Chart AR vs EN", c1)

c2 = BarChart(); c2.type = "bar"; c2.gapWidth = 40
s = Series(Reference(so, min_col=2, min_row=1, max_row=len(order) + 1), title_from_data=True)
fill(s, "A5A5A5"); labels(s, "0.00", "outEnd")
for k, l in enumerate(order):
    if l in ("Arabic", "Kurdish (Sorani)", "Persian", "Urdu"):
        p = DataPoint(idx=k); p.graphicalProperties = GraphicalProperties(solidFill="ED7D31" if l == "Arabic" else "FFC000"); s.dPt.append(p)
    if l == "English":
        p = DataPoint(idx=k); p.graphicalProperties = GraphicalProperties(solidFill="4472C4"); s.dPt.append(p)
c2.series.append(s)
c2.set_categories(Reference(so, min_col=1, min_row=2, max_row=len(order) + 1))
c2.x_axis.scaling.orientation = "maxMin"; c2.legend = None; c2.y_axis.title = "Tokens ÷ English tokens"
style(c2, "Token tax of 24 languages on Llama 4 (orange = Arabic, gold = other Arabic-script)", 24, 16)
chart_sheet(wb, "Chart Languages", c2)

c3 = ScatterChart(); c3.style = 13
for k, n in enumerate(TOK, 2):
    s = Series(Reference(ft, min_col=5, min_row=k), Reference(ft, min_col=4, min_row=k), title=n)
    s.marker.symbol = "circle"; s.marker.size = 12
    s.marker.graphicalProperties = GraphicalProperties(solidFill=OFFICE[k - 2]); s.marker.graphicalProperties.line.solidFill = OFFICE[k - 2]
    s.graphicalProperties = GraphicalProperties(); s.graphicalProperties.line.noFill = True
    c3.series.append(s)
c3.x_axis.title = "Share of the vocabulary in Arabic script"; c3.x_axis.numFmt = "0%"
c3.y_axis.title = "Arabic ÷ English tokens"; c3.y_axis.scaling.min = 0.8
c3.x_axis.scaling.logBase = 10; c3.x_axis.scaling.min = 0.0003; c3.x_axis.scaling.max = 0.1
c3.legend.position = "r"
style(c3, "More Arabic in the vocabulary, lower tax (log x-axis)")
chart_sheet(wb, "Chart Vocab vs Tax", c3)

me = ["Arabic", "Kurdish (Sorani)", "Persian", "Urdu", "Hebrew", "Turkish"]
rd = wb.create_sheet("Radar Data")
sel = ["Llama 3", "Llama 4", "Gemma 3", "Mistral Tekken"]
header(rd, 1, ["Language"] + sel, [18] + [12] * 4)
for i, l in enumerate(me, 2):
    rd.cell(i, 1, l)
    for j, n in enumerate(sel, 2):
        rd.cell(i, j, f"=Parity!{COL[n]}{ROW[l]}").number_format = "0.00"
c4 = RadarChart(); c4.type = "marker"
c4.add_data(Reference(rd, min_col=2, min_row=1, max_col=5, max_row=len(me) + 1), titles_from_data=True)
c4.set_categories(Reference(rd, min_col=1, min_row=2, max_row=len(me) + 1))
for s, colr in zip(c4.series, ["A5A5A5", "4472C4", "70AD47", "ED7D31"]):
    fill(s, colr, line=True, width=31750)
c4.y_axis.delete = False
c4.legend.position = "b"
style(c4, "Languages of the region: token tax on four tokenizers (smaller is better)", 20, 14)
chart_sheet(wb, "Chart Region", c4)

c5 = BarChart(); c5.type = "col"; c5.gapWidth = 50
for col, colr in ((2, "ED7D31"), (3, "4472C4")):
    s = Series(Reference(fh, min_col=col, min_row=1, max_row=7), title_from_data=True)
    fill(s, colr); labels(s, "0%", "outEnd"); c5.series.append(s)
c5.set_categories(Reference(fh, min_col=1, min_row=2, max_row=7))
c5.y_axis.numFmt = "0%"; c5.y_axis.title = "Share of words"; c5.x_axis.title = "Tokens needed for one word (Llama 4)"
c5.legend.position = "b"
style(c5, "Most English words are one token; most Arabic words are not")
chart_sheet(wb, "Chart Words", c5)

ot = wb.create_sheet("Time Data")
langs_t = ["Arabic", "Persian", "Urdu", "Hindi", "French"]
header(ot, 1, ["Tokenizer"] + langs_t, [26] + [10] * len(langs_t))
for i, t in enumerate(R["tokenizers"], 2):
    ot.cell(i, 1, f"{t['name']} ({t['year']})")
    for j, l in enumerate(langs_t, 2):
        ot.cell(i, j, f"=Parity!{COL[t['name']]}{ROW[l]}").number_format = "0.00"
c6 = LineChart()
c6.add_data(Reference(ot, min_col=2, min_row=1, max_col=1 + len(langs_t), max_row=NT), titles_from_data=True)
c6.set_categories(Reference(ot, min_col=1, min_row=2, max_row=NT))
for s, colr, sym in zip(c6.series, ["ED7D31", "FFC000", "70AD47", "7030A0", "4472C4"], ["circle", "diamond", "square", "triangle", "x"]):
    fill(s, colr, line=True); s.marker.symbol = sym; s.marker.size = 8
    s.marker.graphicalProperties = GraphicalProperties(solidFill=colr); s.marker.graphicalProperties.line.solidFill = colr
c6.y_axis.title = "Tokens ÷ English"; c6.legend.position = "b"
style(c6, "From GPT-2 to Llama 4: the tax has fallen, but not to 1")
chart_sheet(wb, "Chart Over Time", c6)

c7 = BarChart(); c7.type = "bar"; c7.grouping = "percentStacked"; c7.overlap = 100; c7.gapWidth = 40
for j, (s_, colr) in enumerate(zip(scripts, ["4472C4", "7030A0", "ED7D31", "FFC000", "70AD47", "A5A5A5"]), 2):
    s = Series(Reference(sc, min_col=j, min_row=1, max_row=NT), title_from_data=True); fill(s, colr); c7.series.append(s)
c7.set_categories(Reference(sc, min_col=1, min_row=2, max_row=NT))
c7.x_axis.scaling.orientation = "maxMin"; c7.legend.position = "b"; c7.y_axis.numFmt = "0%"
style(c7, "What each vocabulary is made of, by writing system")
chart_sheet(wb, "Chart Vocab Scripts", c7)

c8 = DoughnutChart(holeSize=55)
row_t = TOK.index("Mistral Tekken") + 2
c8.add_data(Reference(sc, min_col=2, min_row=row_t, max_col=1 + len(scripts), max_row=row_t), from_rows=True, titles_from_data=False)
c8.set_categories(Reference(sc, min_col=2, min_row=1, max_col=1 + len(scripts), max_row=1))
for k, colr in enumerate(["4472C4", "7030A0", "ED7D31", "FFC000", "70AD47", "A5A5A5"]):
    p = DataPoint(idx=k); p.graphicalProperties = GraphicalProperties(solidFill=colr); c8.series[0].dPt.append(p)
c8.dataLabels = DataLabelList(); c8.dataLabels.showPercent = True
for k in ("showVal", "showCatName", "showSerName", "showLegendKey"):
    setattr(c8.dataLabels, k, False)
c8.legend.position = "r"
style(c8, "Mistral Tekken, the most Arabic-friendly vocabulary here", 18, 12)
chart_sheet(wb, "Chart Tekken Donut", c8)

c9 = BarChart(); c9.type = "col"; c9.gapWidth = 60
for col, colr in ((10, "4472C4"), (11, "ED7D31")):
    s = Series(Reference(ft, min_col=col, min_row=1, max_row=NT), title_from_data=True)
    fill(s, colr); labels(s, "0", "outEnd"); c9.series.append(s)
c9.set_categories(Reference(ft, min_col=1, min_row=2, max_row=NT))
c9.y_axis.title = "Tokens for 10 numbers"; c9.legend.position = "b"
style(c9, "Western vs Eastern Arabic digits: tokens for the same 10 numbers")
chart_sheet(wb, "Chart Digits", c9)

c10 = BarChart(); c10.type = "col"; c10.gapWidth = 50
for col, colr in ((2, "4472C4"), (3, "ED7D31"), (4, "70AD47")):
    s = Series(Reference(di, min_col=col, min_row=1, max_row=NT), title_from_data=True)
    fill(s, colr); labels(s, "0", "outEnd"); c10.series.append(s)
c10.set_categories(Reference(di, min_col=1, min_row=2, max_row=NT))
c10.y_axis.title = f"Tokens for {R['dialect_sentences']} sentences"; c10.legend.position = "b"
style(c10, "English, Standard Arabic and Iraqi Arabic: same 12 sentences")
chart_sheet(wb, "Chart Dialect", c10)

c11 = BarChart(); c11.type = "bar"; c11.gapWidth = 50
s = Series(Reference(cc, min_col=3, min_row=7, max_row=7 + len(TOK)), title_from_data=True)
fill(s, "C00000"); labels(s, '"$"#,##0', "outEnd"); c11.series.append(s)
c11.set_categories(Reference(cc, min_col=1, min_row=8, max_row=7 + len(TOK)))
c11.x_axis.scaling.orientation = "maxMin"; c11.legend = None; c11.y_axis.numFmt = '"$"#,##0'; c11.y_axis.title = "Extra USD per month"
style(c11, "Extra monthly cost of 100M English-token-equivalents written in Arabic, at $2/MTok")
chart_sheet(wb, "Chart Cost", c11)

ar = ROW["Arabic"]
tiles(wb, [(f"=Parity!{COL['Llama 4']}{ar}-1", "+0%", "More Arabic tokens, Llama 4", "F4B183"),
           (f"=Parity!{COL['GPT-2']}{ar}", '0.0"×"', "Arabic tax on GPT-2", "FF7C80"),
           (f"=Parity!{COL['Mistral Tekken']}{ar}-1", "+0%", "Lowest tax: Mistral Tekken", "A9D18E"),
           ("='Tokenizer Data'!F8", '0.0', "Arabic tokens/word, Llama 4", "9DC3E6")])
pathlib.Path("excel").mkdir(exist_ok=True)
order_s = ["Overview", "Cost Calculator", "Chart AR vs EN", "Parity", "Chart Languages", "Chart Vocab vs Tax", "Chart Region", "Chart Words",
           "Chart Over Time", "Chart Vocab Scripts", "Chart Tekken Donut", "Chart Digits", "Chart Dialect", "Chart Cost",
           "Tokens", "Tokenizer Data", "Ranking Data", "Words Data", "Scripts Data", "Dialect Data", "Radar Data", "Time Data"]
wb._sheets = [wb[n] for n in order_s]
wb.save("excel/arabic_token_tax.xlsx")
print("saved")
