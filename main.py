import os
import io
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from jinja2 import Template
from weasyprint import HTML, CSS

app = FastAPI()

# Input schemas
class PartItem(BaseModel):
    part_num: Optional[str] = ""
    description: Optional[str] = ""
    qty: Optional[int] = 0
    price: Optional[float] = 0.0

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
    rate: Optional[float] = 0.0

class QuotationPayload(BaseModel):
    date: Optional[str] = ""
    wo_num: Optional[str] = ""
    cust_name: Optional[str] = ""
    address: Optional[str] = ""
    phone: Optional[str] = ""
    tech: Optional[str] = "Adam"
    comments: Optional[str] = ""
    equipment: Optional[List[EquipmentItem]] = []
    labour: Optional[List[LabourItem]] = []

# Embedded Jinja2 HTML Template with layout fixes
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

  /* Fixed layout tables to strictly constrain width within 100% */
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

  .summary-table {
    width: 40%;
    margin-left: auto;
    table-layout: fixed;
    border-collapse: collapse;
    margin-top: 8px;
  }

  .summary-table td {
    border: 1px solid #000;
    padding: 4px 6px;
  }

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
        <td colspan="3">{{ address }}</td>
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
        <col style="width: 25%;">
        <col style="width: 45%;">
        <col style="width: 12%;">
        <col style="width: 18%;">
      </colgroup>
      <thead>
        <tr>
          <th>PART #</th>
          <th>DESCRIPTION</th>
          <th class="text-center">QTY</th>
          <th class="text-right">PRICE</th>
        </tr>
      </thead>
      <tbody>
        {% for part in item.parts %}
        <tr>
          <td>{{ part.part_num }}</td>
          <td>{{ part.description }}</td>
          <td class="text-center">{{ part.qty }}</td>
          <td class="text-right">${{ "%.2f"|format(part.price) }}</td>
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
      <col style="width: 20%;">
      <col style="width: 50%;">
      <col style="width: 12%;">
      <col style="width: 18%;">
    </colgroup>
    <thead>
      <tr>
        <th>LABOUR CODE</th>
        <th>DESCRIPTION</th>
        <th class="text-center">HOURS</th>
        <th class="text-right">PRICE</th>
      </tr>
    </thead>
    <tbody>
      {% for l in labour %}
      <tr>
        <td>{{ l.code }}</td>
        <td>{{ l.description }}</td>
        <td class="text-center">{{ l.hours }}</td>
        <td class="text-right">${{ "%.2f"|format(l.hours * l.rate) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% endif %}

  <table class="summary-table">
    <colgroup>
      <col style="width: 50%;">
      <col style="width: 50%;">
    </colgroup>
    <tr>
      <td class="bold text-right">TOTAL:</td>
      <td class="bold text-right">${{ "%.2f"|format(total_amount) }}</td>
    </tr>
  </table>

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
        # Calculate total parts + labour
        total_amount = 0.0
        for eq in payload.equipment:
            for pt in eq.parts:
                total_amount += (pt.qty or 0) * (pt.price or 0.0)

        for lb in payload.labour:
            total_amount += (lb.hours or 0.0) * (lb.rate or 0.0)

        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(
            date=payload.date,
            wo_num=payload.wo_num,
            cust_name=payload.cust_name,
            address=payload.address,
            phone=payload.phone,
            tech=payload.tech,
            comments=payload.comments,
            equipment=payload.equipment,
            labour=payload.labour,
            total_amount=total_amount
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