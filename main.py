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

# Input schemas without Labour Code/Description
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

class QuotationPayload(BaseModel):
    date: Optional[str] = ""
    wo_num: Optional[str] = ""
    cust_name: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    phone: Optional[str] = ""
    labour_hours: Optional[float] = 0.0
    tech: Optional[str] = "Adam"
    comments: Optional[str] = ""
    equipment: Optional[List[EquipmentItem]] = []

# Embedded Jinja2 HTML Template styled for enhanced readability
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  @page {
    size: letter;
    margin: 14mm 14mm 14mm 14mm;
  }
  
  * {
    box-sizing: border-box;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  }
  
  body {
    font-size: 11px;
    line-height: 1.5;
    color: #0f172a;
    margin: 0;
    padding: 0;
  }

  .header-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16px;
  }

  .header-table td {
    vertical-align: middle;
  }

  .title-main {
    font-size: 20px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #1e293b;
  }

  .meta-info {
    font-size: 11px;
    color: #334155;
  }

  .info-box {
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    background-color: #f8fafc;
    padding: 8px 12px;
    margin-bottom: 14px;
    width: 100%;
  }

  .info-table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
  }

  .info-table td {
    padding: 4px 6px;
    vertical-align: top;
    word-wrap: break-word;
  }

  .section-header {
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    font-size: 11px;
    padding: 6px 10px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 14px;
    margin-bottom: 8px;
  }

  .equip-box {
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    margin-bottom: 10px;
    padding: 10px 12px;
  }

  .equip-row {
    margin-bottom: 4px;
    font-size: 11px;
  }

  table.data-table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
    margin-top: 8px;
    margin-bottom: 4px;
  }

  table.data-table th, table.data-table td {
    border: 1px solid #cbd5e1;
    padding: 6px 8px;
    text-align: left;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  table.data-table th {
    background-color: #f8fafc;
    font-size: 10px;
    font-weight: 700;
    color: #334155;
    text-transform: uppercase;
  }

  .labour-box {
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 10px 12px;
    margin-bottom: 12px;
    background-color: #ffffff;
    font-size: 12px;
  }

  .text-right { text-align: right; }
  .text-center { text-align: center; }
  .bold { font-weight: 700; color: #1e293b; }

  .comments-box {
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 8px 10px;
    min-height: 48px;
    margin-top: 4px;
    word-wrap: break-word;
    background-color: #ffffff;
    font-size: 11px;
  }

  .footer-row {
    margin-top: 12px;
    font-size: 11px;
  }
</style>
</head>
<body>

  <table class="header-table">
    <tr>
      <td>
        <div class="title-main">Service Quotation</div>
      </td>
      <td class="text-right meta-info">
        <div><span class="bold">Date:</span> {{ date }}</div>
        <div><span class="bold">Work Order #:</span> {{ wo_num }}</div>
      </td>
    </tr>
  </table>

  <div class="info-box">
    <table class="info-table">
      <colgroup>
        <col style="width: 16%;">
        <col style="width: 44%;">
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
    <div class="bold" style="margin-top: 8px; margin-bottom: 2px;">PARTS REQUIRED:</div>
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

  <div class="section-header">Labour</div>
  <div class="labour-box">
    <span class="bold">Estimated Labour:</span> {{ labour_hours }} {{ 'hour' if labour_hours == 1 or labour_hours == 1.0 else 'hours' }}
  </div>

  <div class="footer-row"><span class="bold">SERVICE TECH:</span> {{ tech }}</div>

  <div class="footer-row"><span class="bold">ADDITIONAL COMMENTS:</span></div>
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
            labour_hours=payload.labour_hours,
            tech=payload.tech,
            comments=payload.comments,
            equipment=payload.equipment
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
