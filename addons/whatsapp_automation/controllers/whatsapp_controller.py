from odoo import http
from odoo.http import request


class WhatsAppInvoiceController(http.Controller):

    @http.route(
        "/whatsapp/invoice/<int:move_id>",
        type="http",
        auth="public",
        website=False
    )
    def whatsapp_invoice_pdf(self, move_id, token=None, **kwargs):

        move = request.env["account.move"].sudo().browse(move_id)

        # Validaciones básicas
        if not move.exists():
            return request.not_found()

        if move.move_type != "out_invoice":
            return request.not_found()

        # Validar token
        if not token or token != move.whatsapp_access_token:
            return request.not_found()

        # ✅ REPORTE CORRECTO EN ODOO 19
        report = request.env.ref("account.account_invoices")

        pdf_content, _ = report._render_qweb_pdf([move.id])

        headers = [
            ("Content-Type", "application/pdf"),
            ("Content-Disposition", f'attachment; filename="{move.name}.pdf"'),
        ]

        return request.make_response(pdf_content, headers=headers)
