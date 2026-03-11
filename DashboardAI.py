
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from langchain_community.llms import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

# Load free LLM (e.g., Mistral-7B - runs on CPU/GPU)
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200)
llm = HuggingFacePipeline(pipeline=pipe)

# Sample data (replace with your CSV/Excel)
df = pd.DataFrame({
    'Month': ['Jan', 'Feb', 'Mar', 'Apr'],
    'Sales': [100, 150, 120, 180],
    'Region': ['North', 'South', 'North', 'South']
})

# AI Agent: Analyze and suggest dashboard elements
prompt_template = PromptTemplate(
    input_variables=["data_summary"],
    template="""Analyze this data summary: {data_summary}
Suggest 2-3 dashboard elements (charts/tables) with exact instructions like:
1. Bar chart: Sales by Month (column A vs B)
2. Pie chart: Sales by Region (group C)
3. Summary table: Total sales by region
Respond ONLY with numbered instructions."""
)

chain = LLMChain(llm=llm, prompt=prompt_template)
data_summary = df.describe().to_string() + "Columns: " + str(df.columns.tolist())
instructions = chain.run(data_summary)
print("AI Suggestions:", instructions)
# e.g., "1. Bar chart: Sales by Month..."

# Create Excel dashboard (parse AI instructions or use defaults)
wb = Workbook()
ws_data = wb.active
ws_data.title = 'Data'
for r, row in enumerate(df.itertuples(index=False), 1):
    for c, value in enumerate(row, 1):
        ws_data.cell(row=r, column=c, value=value)

ws_dash = wb.create_sheet('Dashboard')
ws_dash['A1'] = 'AI-Generated Sales Dashboard'

# AI-driven charts (parse instructions or auto-generate based on trends)
# Example: Detect upward trend → Line chart
if df['Sales'].is_monotonic_increasing:
    chart = LineChart()
else:
    chart = BarChart()
data_ref = Reference(ws_data, min_col=2, min_row=1, max_row=len(df) + 1, max_col=2)
cats = Reference(ws_data, min_col=1, min_row=2, max_row=len(df) + 1)
chart.add_data(data_ref)
chart.set_categories(cats)
chart.title = 'AI Selected: Sales Trend'
ws_dash.add_chart(chart, 'E5')

# Summary table (Pivot-like)
pivot = df.pivot_table(values='Sales', index='Region', aggfunc='sum')
for r, (region, total) in enumerate(pivot.iterrows(), 6):
    ws_dash[f'A{r}'] = region
    ws_dash[f'B{r}'] = total

wb.save('ai_dashboard.xlsx')
print("AI dashboard saved! Opens in Excel 2007")
