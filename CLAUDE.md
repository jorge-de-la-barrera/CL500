# CLAUDE.md

## Proyecto

Sistema de monitorización de anuncios Honda CL500.

## Objetivos

- Scraping robusto de honda.appmoto.net
- Persistencia SQLite
- Historial temporal de cambios
- Detección de anuncios nuevos/desaparecidos
- Exportación CSV
- Automatización diaria
- Dockerización futura

## Arquitectura

```text
cl500_monitor/
    scraper.py
    database.py
    parsers/
    models/
    exporters/
```

## Requisitos técnicos

- Python 3.12+
- Tipado estricto
- Código SOLID
- Evitar parsers frágiles dependientes de clases CSS volátiles
- Mantener HTML/raw text para trazabilidad

## Futuras mejoras

- Playwright/Selenium si aparece JS dinámico
- Notificaciones Telegram
- Dashboard Streamlit
- Tracking de precio histórico
- Tests pytest
- CI/CD GitHub Actions
