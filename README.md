# CL500 Monitor

Sistema de monitorización de anuncios Honda CL500 en `honda.appmoto.net`.

## Objetivo

Recuperar anuncios de Honda CL500, almacenar sus datos en SQLite y mantener un histórico para detectar:

- anuncios nuevos
- cambios de precio
- cambios en kilometraje, extras o descripción
- desaparición de anuncios

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso básico

```bash
python -m cl500_monitor.scraper
```

Por defecto crea la base de datos en:

```text
data/cl500.sqlite
```

## Uso con parámetros

```bash
python -m cl500_monitor.scraper --db data/cl500.sqlite --query "CL500"
```

## Automatización diaria

Ejemplo con cron:

```cron
15 8 * * * cd /ruta/CL500 && .venv/bin/python -m cl500_monitor.scraper --db data/cl500.sqlite
```

## Nota

El HTML real de `honda.appmoto.net` puede cambiar. El scraper está diseñado de forma conservadora: intenta extraer datos estructurados, pero conserva también el texto fuente del anuncio para poder ajustar parsers sin perder trazabilidad.
