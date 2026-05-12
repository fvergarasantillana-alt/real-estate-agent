# Workflow: Onboarding de Nuevo Cliente

## Objetivo
Configurar el sistema completo (landing page + bot de WhatsApp) para un nuevo agente de bienes raíces. Al finalizar, el cliente tiene una landing page personalizada y un bot de WhatsApp que pre-califica leads y le notifica en tiempo real.

## Tiempo estimado
- Setup técnico: 1-2 horas
- Verificación del número en Meta: minutos (si FV Agency ya está verificada)
- Prueba end-to-end: 30 minutos

---

## Fase 1: Intake — Recopilar datos del cliente

Hacer estas preguntas al cliente antes de empezar cualquier configuración:

### Información del agente
- Nombre completo
- Título profesional en inglés (ej: "Miami Real Estate Agent")
- Título profesional en español (ej: "Agente de Bienes Raíces en Miami")
- Bio en inglés (2-3 oraciones: experiencia, especialidad, qué lo hace diferente)
- Bio en español (misma bio traducida)
- Zonas de Miami que cubre en inglés (ej: "Doral, Hialeah, Miami Lakes")
- Zonas de Miami que cubre en español (ej: "Doral, Hialeah, Miami Lakes")
- Número de WhatsApp de negocios (con código de país, ej: `17865551234`)
- Email de negocios

### Marca visual
- Foto profesional en alta resolución
- ¿Tiene colores de marca? Si sí, pedir los hex codes (ej: `#1a4f7a`, `#e8a020`)
- Si no tiene colores: elegir estilo
  - A) Elegante y minimalista (blanco + color oscuro de acento)
  - B) Cálida y personal (tonos tierra/dorados)
  - C) Moderna y bold (colores fuertes, alto contraste)
- Stats a destacar (opcional): número de propiedades vendidas, años de experiencia, volumen de ventas

### Servicios que ofrece
Marcar los que aplican: Compra / Venta / Renta / Inversión / Relocation

### Técnico
- Email de Gmail para notificaciones (o crear uno nuevo dedicado)
- ¿Quiere dominio personalizado? (ej: `daniana.com`, costo ~$10-15/año en namecheap.com)

---

## Fase 2: Setup técnico

### 2a. Crear proyecto en Vercel

**Cliente estándar (sin customizaciones de código):**
1. vercel.com → Add New Project → importar repo `real-estate-agent`
2. Framework: Other, Root directory: `/`
3. Deploy (el primero fallará — normal, aún no tiene env vars)

**Cliente con customizaciones especiales (cobrar extra):**
1. Hacer fork del repo en GitHub → `real-estate-{nombre-cliente}`
2. Crear proyecto en Vercel apuntando al fork
3. Los cambios de código se hacen en ese fork sin afectar a otros clientes

### 2b. Configurar variables de entorno en Vercel

Ir a Vercel → Project → Settings → Environment Variables y agregar:

| Variable | Valor | Notas |
|---|---|---|
| `AGENT_NAME` | Nombre del agente | |
| `AGENT_TITLE_EN` | Título en inglés | |
| `AGENT_TITLE_ES` | Título en español | |
| `AGENT_BIO_EN` | Bio en inglés | |
| `AGENT_BIO_ES` | Bio en español | |
| `AGENT_AREAS_EN` | Zonas en inglés | |
| `AGENT_AREAS_ES` | Zonas en español | |
| `AGENT_WHATSAPP_NUMBER` | Número sin `+` | ej: `17865551234` |
| `AGENT_EMAIL` | Email del agente | Para recibir notificaciones |
| `GMAIL_USER` | Gmail para enviar notificaciones | |
| `GMAIL_APP_PASSWORD` | App Password de Gmail | Gmail → Seguridad → App Passwords |
| `ANTHROPIC_API_KEY` | API key de Anthropic | Puede compartirse entre clientes |
| `RAPIDAPI_KEY` | API key de RapidAPI | Puede compartirse entre clientes |
| `META_WHATSAPP_TOKEN` | Token de Meta | Ver Fase 3 |
| `META_PHONE_NUMBER_ID` | ID del número en Meta | Ver Fase 3 |
| `META_VERIFY_TOKEN` | `my-verify-token-change-this` | Puede ser el mismo para todos |
| `META_APP_SECRET` | App Secret de Meta | Ver Fase 3 |

### 2c. Subir foto del agente

```bash
# Renombrar la foto y subirla al repo
cp foto-cliente.jpg public/static/img/{nombre-cliente}.jpg
git add public/static/img/{nombre-cliente}.jpg
git commit -m "Add agent photo: {nombre-cliente}"
git push
```

Vercel redeploya automáticamente al hacer push.

---

## Fase 3: Configurar Meta WhatsApp

### 3a. Agregar número del cliente a FV Agency

> **Nota:** FV Agency solo necesita verificarse una vez. Para cada cliente nuevo solo se agrega su número — no hay nueva verificación del negocio.

1. developers.facebook.com → app "Real Estate Agent" → WhatsApp → Phone Numbers
2. Click "Add phone number"
3. Ingresar el número del cliente
4. Meta envía código de verificación por SMS al número del cliente
5. Ingresar el código → número verificado
6. Copiar el **Phone Number ID** que aparece → pegarlo en Vercel como `META_PHONE_NUMBER_ID`

### 3b. Configurar webhook

1. Meta for Developers → app → WhatsApp → Configuration
2. Callback URL: `https://{proyecto-vercel}.vercel.app/api/whatsapp`
3. Verify token: `my-verify-token-change-this`
4. Click "Verify and save"
5. En Webhook fields → `messages` → Subscribe

### 3c. Copiar App Secret y Token temporal

1. Meta for Developers → app → Settings → Basic → App Secret → Show → copiar
2. Pegar en Vercel como `META_APP_SECRET`
3. Meta for Developers → app → WhatsApp → API Setup → copiar el Temporary access token
4. Pegar en Vercel como `META_WHATSAPP_TOKEN` (temporal, dura 24h)

### 3d. Generar token permanente

1. business.facebook.com → Settings → Users → System Users → "WhatsApp Bot"
2. Generate new token → seleccionar app → Never expire
3. Permisos: `whatsapp_business_messaging`, `whatsapp_business_management`
4. Copiar token → actualizar `META_WHATSAPP_TOKEN` en Vercel
5. Redeploy

---

## Fase 4: Prueba end-to-end

1. Abrir la landing page del cliente (`https://{proyecto}.vercel.app`) — verificar que carga con sus datos
2. Mandar mensaje al número del cliente desde un WhatsApp de prueba: "Hola, quiero comprar una casa"
3. Verificar que el bot responde con el flujo de pre-calificación
4. Completar las 9 preguntas con datos ficticios
5. Verificar que el cliente recibe el email de notificación en español
6. Verificar que el cliente recibe el WhatsApp de notificación

---

## Fase 5: Entrega

1. Compartir la URL de la landing page con el cliente
2. Darle el número de WhatsApp del bot para que lo pruebe
3. Explicarle qué información recibe en cada notificación de lead
4. Si quiere dominio personalizado: ver `workflows/deploy.md` → sección "Custom Domain"

---

## Fase 6: Customizaciones adicionales (cobrar extra)

Requieren hacer fork del repo y cambios de código:

- Modificar el flujo de pre-calificación (más/menos preguntas, preguntas distintas)
- Integración con CRM (Salesforce, HubSpot, etc.)
- Bot solo en inglés o en otro idioma
- Rediseño completo de la landing page
- Notificaciones a múltiples personas (equipo del agente)
- Integración con calendario para agendar visitas automáticamente

---

## Update Log
- 2026-05-12: Workflow inicial creado. Google Sheets eliminado del proceso — el bot usa Zillow API en tiempo real.
