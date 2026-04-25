import os

AGENT_NAME     = os.environ.get('AGENT_NAME',     'Daniana Santillana')
AGENT_TITLE_EN = os.environ.get('AGENT_TITLE_EN', 'Miami Real Estate Agent')
AGENT_TITLE_ES = os.environ.get('AGENT_TITLE_ES', 'Agente de Bienes Raíces en Miami')
AGENT_AREAS_EN = os.environ.get('AGENT_AREAS_EN', 'All of Miami-Dade County')
AGENT_AREAS_ES = os.environ.get('AGENT_AREAS_ES', 'Todo el Condado de Miami-Dade')
AGENT_BIO_EN   = os.environ.get('AGENT_BIO_EN',
    "I'm Daniana Santillana — a Peruvian-born real estate agent, proud Latina, and mother "
    "based in Miami. Over the past two-plus years, I've had the privilege of working alongside "
    "high-profile clients and closing significant deals across Miami-Dade County. But what truly "
    "drives me is the families. I've guided dozens of families who arrived in this country with "
    "big dreams and very specific needs — people starting fresh, navigating an unfamiliar market, "
    "looking for a place that finally felt like home. I listen closely, I advocate fiercely, and "
    "I don't stop until I find the right fit."
)
AGENT_BIO_ES   = os.environ.get('AGENT_BIO_ES',
    "Soy Daniana Santillana — agente inmobiliaria nacida en Perú, latina orgullosa y mamá, "
    "con base en Miami. En más de dos años en esta industria, he tenido el privilegio de trabajar "
    "con clientes de alto perfil y cerrar negocios importantes en todo el Condado de Miami-Dade. "
    "Pero lo que realmente me mueve son las familias. He acompañado a decenas de familias que "
    "llegaron a este país con grandes sueños y necesidades muy específicas — personas que empezaban "
    "de cero, navegando un mercado desconocido, buscando un lugar que por fin se sintiera como hogar. "
    "Escucho con atención, defiendo con determinación y no me detengo hasta encontrar la opción "
    "correcta."
)

COPY = {
    "en": {
        "nav_listings":       "Listings",
        "nav_about":          "About",
        "nav_contact":        "Contact",
        "hero_headline":      f"Find Your Perfect Home in {AGENT_AREAS_EN.split(',')[0]}",
        "hero_subheadline":   f"Expert guidance for buyers, sellers, and renters across {AGENT_AREAS_EN}.",
        "hero_cta_whatsapp":  "Chat on WhatsApp",
        "hero_cta_contact":   "Get in Touch",
        "listings_title":     "Featured Listings",
        "listings_subtitle":  f"Current properties available in {AGENT_AREAS_EN}.",
        "listings_empty":     "No listings available right now. Check back soon!",
        "about_title":        "About Me",
        "about_bio":          AGENT_BIO_EN,
        "about_areas":        f"Areas covered: {AGENT_AREAS_EN}",
        "services_title":     "How I Can Help",
        "contact_title":      "Get in Touch",
        "contact_subtitle":   "Send me a message and I'll get back to you within 24 hours.",
        "contact_success":    "Message sent! I'll be in touch shortly.",
        "footer_rights":      "All rights reserved.",
    },
    "es": {
        "nav_listings":       "Propiedades",
        "nav_about":          "Sobre Mí",
        "nav_contact":        "Contacto",
        "hero_headline":      f"Encuentra Tu Hogar Perfecto en {AGENT_AREAS_ES.split(',')[0]}",
        "hero_subheadline":   f"Asesoría experta para compradores, vendedores y arrendatarios en {AGENT_AREAS_ES}.",
        "hero_cta_whatsapp":  "Escríbeme por WhatsApp",
        "hero_cta_contact":   "Contáctame",
        "listings_title":     "Propiedades Destacadas",
        "listings_subtitle":  f"Propiedades disponibles actualmente en {AGENT_AREAS_ES}.",
        "listings_empty":     "No hay propiedades disponibles por ahora. ¡Vuelve pronto!",
        "about_title":        "Sobre Mí",
        "about_bio":          AGENT_BIO_ES,
        "about_areas":        f"Áreas de cobertura: {AGENT_AREAS_ES}",
        "services_title":     "¿Cómo Puedo Ayudarte?",
        "contact_title":      "Contáctame",
        "contact_subtitle":   "Envíame un mensaje y te responderé en menos de 24 horas.",
        "contact_success":    "¡Mensaje enviado! Me pondré en contacto pronto.",
        "footer_rights":      "Todos los derechos reservados.",
    },
}
