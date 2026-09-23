from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from jinja2 import Template
from weasyprint import HTML
import os

app = FastAPI(title="Service Quotation PDF Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PartItem(BaseModel):
    part_num: str = ""
    description: str = ""
    qty: int = 1
    price: float = 0.0

class EquipmentItem(BaseModel):
    make: str = ""
    model: str = ""
    serial: str = ""
    work_required: str = ""
    parts: List[PartItem] = Field(default_factory=list)

class LabourItem(BaseModel):
    code: str = ""
    description: str = ""
    hours: float = 0.0
    rate: float = 0.0

class QuotationRequest(BaseModel):
    date: str = ""
    wo_num: str = ""
    cust_num: str = ""
    cust_name: str = ""
    address: str = ""
    phone: str = ""
    fax: Optional[str] = ""
    email: Optional[str] = ""
    equipment: List[EquipmentItem] = Field(default_factory=list)
    labour: List[LabourItem] = Field(default_factory=list)
    comments: Optional[str] = ""
    tech: str = ""

HTML_PDF_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page { size: letter; margin: 0.4in; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 11px; line-height: 1.4; color: #111111; margin: 0; }
  .pdf-header { width: 100%; border-bottom: 1.5px solid #000000; padding-bottom: 4px; margin-bottom: 8px; }
  .pdf-layout-table { width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 6px; }
  .pdf-layout-table td { padding: 4px 2px; vertical-align: bottom; font-size: 11px; color: #111111; }
  .pdf-line-cell { border-bottom: 1px solid #333333; }
  .pdf-label { font-weight: bold; font-size: 11px; color: #000000; text-transform: uppercase; }
  .pdf-val { font-weight: normal; font-size: 11px; color: #222222; word-break: break-word; }
  .pdf-section-head { background: #e5e7eb; font-weight: bold; padding: 4px 6px; border: 1px solid #333333; margin-top: 10px; font-size: 11px; color: #000000; text-transform: uppercase; page-break-after: avoid; }
  .pdf-equip-block { border: 1px solid #333333; padding: 6px 8px; margin-top: 6px; margin-bottom: 8px; background: #fafafa; page-break-inside: avoid; }
  .pdf-table { width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 4px; }
  .pdf-table th, .pdf-table td { border: 1px solid #333333; padding: 4px 6px; text-align: left; font-size: 10px; color: #111111; }
  .pdf-table th { background: #f3f4f6; font-weight: bold; text-transform: uppercase; }
  .pdf-table tr { page-break-inside: avoid; }
  .text-right { text-align: right; }
  .no-break { page-break-inside: avoid; }
</style>
</head>
<body>
  <table class="pdf-layout-table pdf-header">
    <tr>
      <td style="font-size: 16px; font-weight: bold; padding: 0;">SERVICE QUOTATION</td>
      <td class="text-right" style="padding: 0;">
        <span class="pdf-label">DATE:</span> <span class="pdf-val">{{ req.date }}</span>
      </td>
    </tr>
  </table>

  <table class="pdf-layout-table">
    <tr><td colspan="2" class="pdf-line-cell"><span class="pdf-label">WORK ORDER #:</span> <span class="pdf-val">{{ req.wo_num }}</span></td></tr>
    <tr>
      <td style="width: 50%;" class="pdf-line-cell"><span class="pdf-label">CUSTOMER #:</span> <span class="pdf-val">{{ req.cust_num }}</span></td>
      <td style="width: 50%;" class="pdf-line-cell"><span class="pdf-label">CUSTOMER NAME:</span> <span class="pdf-val">{{ req.cust_name }}</span></td>
    </tr>
    <tr><td colspan="2" class="pdf-line-cell"><span class="pdf-label">ADDRESS:</span> <span class="pdf-val">{{ req.address }}</span></td></tr>
    <tr>
      <td style="width: 50%;" class="pdf-line-cell"><span class="pdf-label">PHONE #:</span> <span class="pdf-val">{{ req.phone }}</span></td>
      <td style="width: 50%;" class="pdf-line-cell"><span class="pdf-label">FAX #:</span> <span class="pdf-val">{{ req.fax }}</span></td>
    </tr>
    <tr><td colspan="2" class="pdf-line-cell"><span class="pdf-label">EMAIL:</span> <span class="pdf-val">{{ req.email }}</span></td></tr>
  </table>

  <div class="pdf-section-head">EQUIPMENT & PARTS REQUIRED</div>
  {% for item in req.equipment %}
  <div class="pdf-equip-block">
    <table class="pdf-layout-table" style="margin-bottom:0;">
      <tr>
        <td style="width: 50%;" class="pdf-line-cell"><span class="pdf-label">MAKE:</span> <span class="pdf-val">{{ item.make }}</span></td>
        <td style="width: 50%;" class="pdf-line-cell"><span class="pdf-label">MODEL:</span> <span class="pdf-val">{{ item.model }}</span></td>
      </tr>
      <tr><td colspan="2" class="pdf-line-cell"><span class="pdf-label">SERIAL #:</span> <span class="pdf-val">{{ item.serial }}</span></td></tr>
      <tr>
        <td colspan="2" style="padding-top: 4px;">
          <span class="pdf-label">WORK REQUIRED:</span>
          <div class="pdf-val" style="padding-left: 2px; margin-top: 2px;">{{ item.work_required }}</div>
        </td>
      </tr>
    </table>

    {% if item.parts %}
    <div style="margin-top: 6px;">
      <span class="pdf-label" style="font-size: 10px;">PARTS REQUIRED:</span>
      <table class="pdf-table" style="margin-top: 2px;">
        <thead>
          <tr>
            <th style="width: 25%;">PART #</th>
            <th style="width: 45%;">DESCRIPTION</th>
            <th style="width: 12%;">QTY</th>
            <th style="width: 18%;">PRICE</th>
          </tr>
        </thead>
        <tbody>
          {% for part in item.parts %}
          <tr>
            <td>{{ part.part_num }}</td>
            <td>{{ part.description }}</td>
            <td>{{ part.qty }}</td>
            <td>${{ "%.2f"|format(part.price) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% endif %}
  </div>
  {% endfor %}

  <div class="pdf-section-head">LABOUR CHARGES</div>
  <table class="pdf-table">
    <thead>
      <tr>
        <th style="width: 25%;">LABOUR CHARGES</th>
        <th style="width: 45%;">DESCRIPTION</th>
        <th style="width: 12%;"># OF HOURS</th>
        <th style="width: 18%;">PRICE</th>
      </tr>
    </thead>
    <tbody>
      {% for lab in req.labour %}
      <tr>
        <td>{{ lab.code }}</td>
        <td>{{ lab.description }}</td>
        <td>{{ lab.hours }}</td>
        <td>${{ "%.2f"|format(lab.rate * lab.hours) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="no-break">
    <table class="pdf-layout-table" style="margin-top: 12px;">
      <tr>
        <td>
          <span class="pdf-label">ADDITIONAL COMMENTS:</span>
          <div style="border-bottom: 1px solid #333333; min-height: 22px; margin-top: 2px; font-weight: bold;" class="pdf-val">
            {{ req.comments }}
          </div>
        </td>
      </tr>
    </table>

    <table class="pdf-layout-table" style="margin-top: 8px; border-top: 1px solid #333333; padding-top: 6px;">
      <tr>
        <td style="width: 50%;"><span class="pdf-label">CUSTOMER ACCEPTED:</span> <span class="pdf-val">[ ] PLEASE CHECK IF ACCEPTED</span></td>
        <td style="width: 50%;"><span class="pdf-label">WORK COMPLETED:</span> <span class="pdf-val">[ ]</span></td>
      </tr>
      <tr>
        <td colspan="2" class="pdf-line-cell" style="padding-top: 6px;">
          <span class="pdf-label">SERVICE TECH:</span> <span class="pdf-val">{{ req.tech }}</span>
        </td>
      </tr>
    </table>
  </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>index.html file not found in directory</h1>"

@app.post("/generate-pdf")
async def generate_pdf_endpoint(payload: QuotationRequest):
    try:
        jinja_tmpl = Template(HTML_PDF_TEMPLATE)
        rendered_html = jinja_tmpl.render(req=payload)
        pdf_bytes = HTML(string=rendered_html).write_pdf()
        
        filename = f"Quotation_{payload.wo_num if payload.wo_num else 'Draft'}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))