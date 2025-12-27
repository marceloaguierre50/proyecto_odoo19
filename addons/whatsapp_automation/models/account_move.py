from odoo import models, fields
import logging
import secrets
from ..services.whatsapp_api import WhatsAppService

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    # 🔐 Token seguro para descarga de factura
    whatsapp_access_token = fields.Char(
        string="WhatsApp Access Token",
        copy=False
    )

    def _generate_whatsapp_token(self):
        """
        Genera un token único y seguro para descarga de factura
        """
        for move in self:
            if not move.whatsapp_access_token:
                move.whatsapp_access_token = secrets.token_urlsafe(32)

    def _get_whatsapp_download_url(self):
        """
        Genera la URL completa para descargar la factura por WhatsApp
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/whatsapp/invoice/{self.id}?token={self.whatsapp_access_token}"

    def action_post(self):
        # ✅ Validación normal de Odoo (NO se toca)
        res = super().action_post()

        ICP = self.env["ir.config_parameter"].sudo()
        TOKEN = ICP.get_param("whatsapp.token")
        PHONE_NUMBER_ID = ICP.get_param("whatsapp.phone_number_id")

        for move in self:
            # Solo facturas de cliente
            if move.move_type != "out_invoice":
                continue

            # 🔐 Generar token de descarga
            move._generate_whatsapp_token()

            partner = move.partner_id

            # Obtener teléfono de forma segura
            phone = (
                getattr(partner, "mobile", False)
                or getattr(partner, "phone", False)
            )

            if not phone:
                _logger.warning(
                    "WhatsApp Automation: factura %s sin teléfono (%s)",
                    move.name,
                    partner.name,
                )
                continue

            # Normalizar teléfono
            phone = (
                phone.replace(" ", "")
                     .replace("-", "")
                     .replace("+", "")
            )

            # Argentina → formato E.164
            if phone.startswith("11"):
                phone = "549" + phone
            elif phone.startswith("9"):
                phone = "54" + phone
            elif not phone.startswith("54"):
                phone = "54" + phone

            # Generar URL de descarga
            download_url = move._get_whatsapp_download_url()

            _logger.info(
                "WhatsApp Automation: enviando TEMPLATE factura %s a %s (%s)",
                move.name,
                partner.name,
                phone,
            )

            try:
                WhatsAppService.send_template(
                    token=TOKEN,
                    phone_number_id=PHONE_NUMBER_ID,
                    to=phone,
                    template_name="invoice_confirmed",
                    lang="es_AR",
                    params=[
                        partner.name,
                        move.name,
                        download_url,
                    ],
                )

                # 📝 Registro en chatter
                move.message_post(
                    body=(
                        f"📲 WhatsApp enviado al cliente<br/>"
                        f"<b>Tel:</b> {phone}<br/>"
                        f"<b>Plantilla:</b> invoice_confirmed<br/>"
                        f"<b>Link descarga:</b> <a href='{download_url}' target='_blank'>{download_url}</a>"
                    )
                )

            except Exception as e:
                _logger.error(
                    "WhatsApp Automation ERROR factura %s: %s",
                    move.name,
                    str(e),
                )

        return res
