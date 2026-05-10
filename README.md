# CL500 Monitor

Sistema de monitorización de anuncios Honda CL500 en `honda.appmoto.net`.

El objetivo es recuperar periódicamente anuncios de Honda CL500, extraer datos estructurados y guardarlos en SQLite para detectar anuncios nuevos, cambios de precio, cambios de kilometraje, cambios de extras o descripción y desaparición de anuncios.

## Estado

Versión inicial funcional. El parser HTML es defensivo porque el marcado real del sitio puede cambiar. Aunque no consiga inferir todos los campos, conserva el texto bruto del anuncio para auditoría y ajuste posterior.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Para desarrollo:

```bash
pip install -e '.[dev]'
```

## Uso

Scraping y actualización de SQLite:

```bash
cl500-monitor scrape --db data/cl500.sqlite
```

Listar anuncios activos:

```bash
cl500-monitor list --db data/cl500.sqlite
```

Listar cambios detectados:

```bash
cl500-monitor changes --db data/cl500.sqlite
```

Usar otra búsqueda o URL base:

```bash
cl500-monitor scrape --db data/cl500.sqlite --query "Honda CL500" --base-url https://honda.appmoto.net
```

## Variables de entorno

```bash
CL500_BASE_URL=https://honda.appmoto.net
CL500_QUERY=CL500
CL500_DB=data/cl500.sqlite
```

## Automatización diaria con cron

```cron
15 8 * * * cd /ruta/CL500 && . .venv/bin/activate && cl500-monitor scrape --db data/cl500.sqlite >> logs/cl500.log 2>&1
```

## Calidad

```bash
python -m pytest
python -m mypy src
python -m ruff check src tests
```

## Estructura

```text
src/cl500_monitor/
  cli.py
  scraper.py
  parser.py
  db.py
  models.py
```

## Nota legal y técnica

Antes de ejecutar scraping intensivo, revisa las condiciones de uso del sitio y usa una frecuencia razonable. Este proyecto está pensado para monitorización personal de baja frecuencia, sin bypass de medidas anti-bot.
