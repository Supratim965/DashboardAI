import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.drawing.image import Image
import matplotlib.pyplot as plt

# Sample data (replace with pd.read_csv('yourfile.csv') or pd.read_excel)
df = pd.DataFrame({
    'Month': ['Jan', 'Feb', 'Mar', 'Apr'],
    'Sales': [100, 150, 120, 180],
    'Region': ['North', 'South', 'North', 'South']
})

# Create workbook and data sheet
wb = Workbook()
ws_data = wb.active
ws_data.title = 'Data'
for r, row in enumerate(df.itertuples(index=False), 1):
    for c, value in enumerate(row, 1):
        ws_data.cell(row=r, column=c, value=value)

# Dashboard sheet
ws_dash = wb.create_sheet('Dashboard')

# Title
ws_dash.merge_cells('A1:D4')
title_cell = ws_dash['A1']
title_cell.value = 'Sales Dashboard'
title_cell.font = Font(bold=True, size=20)
title_cell.alignment = Alignment(horizontal='center')
title_cell.fill = PatternFill('solid', fgColor='2591DB')

# Copy summary table (e.g., totals by region)
summary = df.groupby('Region')['Sales'].sum()
for c, (region, total) in enumerate(summary.items(), 1):
    ws_dash[f'A5'] = 'Region'
    ws_dash[f'B5'] = region
    ws_dash[f'C5'] = total

# Bar chart for sales by month
chart1 = BarChart()
data = Reference(ws_data, min_col=2, min_row=1, max_row=5, max_col=2)
cats = Reference(ws_data, min_col=1, min_row=2, max_row=5)
chart1.add_data(data)
chart1.set_categories(cats)
chart1.title = 'Sales by Month'
ws_dash.add_chart(chart1, 'E5')

wb.save('dashboard.xlsx')