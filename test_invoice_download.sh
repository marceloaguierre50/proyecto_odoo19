#!/bin/bash
# Script para probar la funcionalidad de descarga de facturas

echo "🧪 Probando funcionalidad de descarga de facturas..."
echo ""

docker exec odoo19_day_web odoo shell -d proyecto_day_local --stop-after-init << 'PYEOF'

# Buscar una factura validada
invoice = env['account.move'].search([
    ('move_type', '=', 'out_invoice'),
    ('state', '=', 'posted')
], limit=1)

if not invoice:
    print('⚠️  No se encontró ninguna factura validada para probar')
    print('   Crea y valida una factura primero')
else:
    print(f'📄 Factura encontrada: {invoice.name}')
    print(f'   Cliente: {invoice.partner_id.name}')
    print(f'   Estado: {invoice.state}')
    
    # Generar token si no existe
    if not invoice.whatsapp_access_token:
        print('\n🔐 Generando token de acceso...')
        invoice._generate_whatsapp_token()
        env.cr.commit()
        print('   ✓ Token generado correctamente')
    else:
        print(f'\n   ✓ Token ya existe: {invoice.whatsapp_access_token[:30]}...')
    
    # Generar URL de descarga
    try:
        download_url = invoice._get_whatsapp_download_url()
        print(f'\n🔗 URL de descarga generada:')
        print(f'   {download_url}')
        
        # Verificar base URL
        base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
        if base_url:
            print(f'\n✅ Base URL configurada: {base_url}')
        else:
            print('\n⚠️  Base URL no configurada (web.base.url)')
        
        print('\n✅ Funcionalidad verificada correctamente!')
        print('\n💡 Para probar el endpoint, accede a la URL desde un navegador')
        print(f'   o usa: curl "{download_url}" -o factura.pdf')
        
    except Exception as e:
        print(f'\n❌ Error al generar URL: {str(e)}')
        import traceback
        traceback.print_exc()

PYEOF

echo ""
echo "✅ Prueba completada"

