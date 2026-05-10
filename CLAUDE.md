# CLAUDE.md

## Proyecto

`CL500 Monitor` es una herramienta Python para monitorizar anuncios de Honda CL500 en `honda.appmoto.net`.

## Objetivo funcional

1. Recuperar anuncios relacionados con Honda CL500.
2. Extraer campos relevantes:
   - URL
   - título
   - precio
   - kilometraje
   - año/modelo
   - ubicación
   - concesionario
   - extras, especialmente Pack Travel
   - texto bruto
3. Guardar observaciones en SQLite.
4. Mantener histórico de snapshots.
5. Detectar cambios entre ejecuciones.
6. Permitir ejecución diaria mediante cron, systemd timer o GitHub Actions.

## Comandos

```bash
cl500-monitor scrape --db data/cl500.sqlite
cl500-monitor list --db data/cl500.sqlite
cl500-monitor changes --db data/cl500.sqlite
```

## Arquitectura actual

```text
src/cl500_monitor/
  cli.py       # interfaz de línea de comandos
  scraper.py   # cliente HTTP y estrategia de búsqueda
  parser.py    # extracción defensiva desde HTML
  db.py        # persistencia SQLite y detección de cambios
  models.py    # dataclasses de dominio
```

## Principios de implementación

- No hacer scraping agresivo.
- Mantener trazabilidad: conservar `raw_text` aunque el parser falle parcialmente.
- No asumir que el HTML del sitio es estable.
- Preferir parsers pequeños, testeables y ajustables.
- No perder snapshots históricos.
- Separar extracción, persistencia y CLI.

## Próximas tareas recomendadas

1. Ejecutar contra HTML real de `honda.appmoto.net` y ajustar selectores.
2. Añadir fixture HTML real anonimizado en `tests/fixtures/`.
3. Añadir exportación CSV.
4. Añadir notificaciones por email/Telegram opcionales.
5. Añadir GitHub Actions para tests.
6. Añadir modo `--dry-run`.
7. Añadir tabla de eventos para anuncios desaparecidos.

## Criterios de calidad

Antes de fusionar cambios:

```bash
python -m pytest
python -m mypy src
python -m ruff check src tests
```

## Restricciones

- No incluir credenciales.
- No subir bases SQLite reales.
- No hacer bypass de medidas anti-bot.
- Revisar términos de uso del sitio antes de aumentar frecuencia de ejecución.
