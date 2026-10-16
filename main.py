import os
import io
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from typing import List, Optional
from jinja2 import Template
from weasyprint import HTML

app = FastAPI()

# Input schemas without prices/rates
class PartItem(BaseModel):
    part_num: Optional[str] = ""
    description: Optional[str] = ""
    qty: Optional[int] = 0

class EquipmentItem(BaseModel):
    make: Optional[str] = ""
    model: Optional[str] = ""
    serial: Optional[str] = ""
    work_required: Optional[str] = ""
    parts: Optional[List[PartItem]] = []

class LabourItem(BaseModel):
    code: Optional[str] = ""
    description: Optional[str] = ""
    hours: Optional[float] = 0.0

class QuotationPayload(BaseModel):
    date: Optional[str] = ""
    wo_num: Optional[str] = ""
    cust_name: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    phone: Optional[str] = ""
    tech: Optional[str] = "Adam"
    comments: Optional[str] = ""
    equipment: Optional[List[EquipmentItem]] = []
    labour: Optional[List[LabourItem]] = []

# Embedded Jinja2 HTML Template updated for City and zero-price parts/labour
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  @page {
    size: letter;
    margin: 10mm;
  }
  
  * {
    box-sizing: border-box;
    font-family: Helvetica, Arial, sans-serif;
  }
  
  body {
    font-size: 10px;
    color: #000000;
    margin: 0;
    padding: 0;
  }

  .header-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 8px;
  }

  .header-table td {
    vertical-align: top;
  }

  .title-main {
    font-size: 16px;
    font-weight: bold;
    text-transform: uppercase;
  }

  .info-box {
    border: 1px solid #000;
    padding: 6px;
    margin-bottom: 8px;
    width: 100%;
  }

  .info-table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
  }

  .info-table td {
    padding: 2px 4px;
    vertical-align: top;
    word-wrap: break-word;
  }

  .section-header {
    background-color: #e5e7eb;
    font-weight: bold;
    font-size: 11px;
    padding: 4px 6px;
    border: 1px solid #000;
    text-transform: uppercase;
    margin-top: 8px;
    margin-bottom: 4px;
  }

  .equip-box {
    border: 1px solid #000;
    margin-bottom: 8px;
    padding: 6px;
  }

  .equip-row {
    margin-bottom: 4px;
  }

  table.data-table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
    margin-top: 4px;
    margin-bottom: 6px;
  }

  table.data-table th, table.data-table td {
    border: 1px solid #000;
    padding: 4px 6px;
    text-align: left;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  table.data-table th {
    background-color: #f3f4f6;
    font-size: 9px;
    font-weight: bold;
    text-transform: uppercase;
  }

  .text-right { text-align: right; }
  .text-center { text-align: center; }
  .bold { font-weight: bold; }

  .comments-box {
    border: 1px solid #000;
    padding: 6px;
    min-height: 40px;
    margin-top: 4px;
    word-wrap: break-word;
  }
</style>
</head>
<body>

  <table class="header-table">
    <tr>
      <td>
        <div class="title-main">Service Quotation</div>
      </td>
      <td class="text-right">
        <div><span class="bold">Date:</span> {{ date }}</div>
        <div><span class="bold">Work Order #:</span> {{ wo_num }}</div>
      </td>
    </tr>
  </table>

  <div class="info-box">
    <table class="info-table">
      <colgroup>
        <col style="width: 15%;">
        <col style="width: 45%;">
        <col style="width: 12%;">
        <col style="width: 28%;">
      </colgroup>
      <tr>
        <td class="bold">CUSTOMER:</td>
        <td>{{ cust_name }}</td>
        <td class="bold">PHONE:</td>
        <td>{{ phone }}</td>
      </tr>
      <tr>
        <td class="bold">ADDRESS:</td>
        <td>{{ address }}</td>
        <td class="bold">CITY:</td>
        <td>{{ city }}</td>
      </tr>
    </table>
  </div>

  <div class="section-header">Equipment & Parts Required</div>

  {% for item in equipment %}
  <div class="equip-box">
    <div class="equip-row"><span class="bold">MAKE:</span> {{ item.make }} &nbsp;&nbsp;&nbsp;&nbsp; <span class="bold">MODEL:</span> {{ item.model }}</div>
    <div class="equip-row"><span class="bold">SERIAL #:</span> {{ item.serial }}</div>
    <div class="equip-row"><span class="bold">WORK REQUIRED:</span> {{ item.work_required }}</div>

    {% if item.parts %}
    <div class="bold" style="margin-top: 4px; margin-bottom: 2px;">PARTS REQUIRED:</div>
    <table class="data-table">
      <colgroup>
        <col style="width: 30%;">
        <col style="width: 55%;">
        <col style="width: 15%;">
      </colgroup>
      <thead>
        <tr>
          <th>PART #</th>
          <th>DESCRIPTION</th>
          <th class="text-center">QTY</th>
        </tr>
      </thead>
      <tbody>
        {% for part in item.parts %}
        <tr>
          <td>{{ part.part_num }}</td>
          <td>{{ part.description }}</td>
          <td class="text-center">{{ part.qty }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% endif %}
  </div>
  {% endfor %}

  {% if labour %}
  <div class="section-header">Labour Charges</div>
  <table class="data-table">
    <colgroup>
      <col style="width: 25%;">
      <col style="width: 60%;">
      <col style="width: 15%;">
    </colgroup>
    <thead>
      <tr>
        <th>LABOUR CODE</th>
        <th>DESCRIPTION</th>
        <th class="text-center">HOURS</th>
      </tr>
    </thead>
    <tbody>
      {% for l in labour %}
      <tr>
        <td>{{ l.code }}</td>
        <td>{{ l.description }}</td>
        <td class="text-center">{{ l.hours }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% endif %}

  <div class="bold" style="margin-top: 8px;">SERVICE TECH: {{ tech }}</div>

  <div class="bold" style="margin-top: 8px;">ADDITIONAL COMMENTS:</div>
  <div class="comments-box">
    {{ comments }}
  </div>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>index.html not found</h1>"

@app.post("/generate-pdf")
def generate_pdf(payload: QuotationPayload):
    try:
        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(
            date=payload.date,
            wo_num=payload.wo_num,
            cust_name=payload.cust_name,
            address=payload.address,
            city=payload.city,
            phone=payload.phone,
            tech=payload.tech,
            comments=payload.comments,
            equipment=payload.equipment,
            labour=payload.labour
        )

        pdf_bytes = HTML(string=rendered_html).write_pdf()

        filename = f"Quotation_{payload.wo_num if payload.wo_num else 'Draft'}.pdf"
        sanitized_filename = re.sub(r'[^\w\.-]', '_', filename)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{sanitized_filename}"'}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
