# Automatizar el pipeline con GitHub Actions

Esta guía describe cómo automatizar la actualización del dashboard de Streamlit usando GitHub Actions. El flujo propuesto es:

1. Actions descarga el repositorio y la base DuckDB vigente.
2. Ejecuta la ingesta y las transformaciones de dbt.
3. Guarda la base DuckDB actualizada en el repositorio.
4. Streamlit Community Cloud detecta el cambio en GitHub y vuelve a desplegar la app con los datos nuevos.

## 1. Corregir la carga incremental

En `pipeline/flows.py`, la rama incremental inserta actualmente `df_tickers` en `raw_race_results`. Los datos de precios deben insertarse en `raw_ticker_data`:

```python
con.sql("INSERT INTO raw_race_results SELECT * FROM df_races")
con.sql("INSERT INTO raw_ticker_data SELECT * FROM df_tickers")
```

Si ambas inserciones apuntan a `raw_race_results`, la segunda fallará porque los datos de precios tienen columnas distintas a los resultados de carreras.

## 2. Configurar dbt en el runner

El proyecto dbt usa el perfil `f1_transform`, pero el runner de GitHub Actions no tendrá el archivo local `~/.dbt/profiles.yml`. Hay dos opciones:

- Generar `~/.dbt/profiles.yml` durante el workflow, antes de ejecutar dbt. El perfil debe usar el adaptador DuckDB y apuntar a `data/f1_market.duckdb` dentro del runner.
- Configurar dbt para leer un perfil guardado en el repositorio. Así se puede compartir la configuración entre el entorno local y Actions; evita incluir rutas absolutas que solo existan en tu computadora.

En cualquier opción, asegúrate de que dbt use el mismo archivo DuckDB que actualiza el pipeline. `pipeline.flows` ya ejecuta `dbt run` al terminar la ingesta; puedes dejarlo ahí o ejecutarlo como paso separado del workflow, pero no hace falta correrlo dos veces.

## 3. Conservar la base actualizada

Los runners de GitHub Actions son temporales: sus cambios locales se pierden al finalizar el job. Como el dashboard lee `data/f1_market.duckdb` del repositorio y el archivo ya está versionado, la opción directa es hacer que el workflow:

1. Ejecute la ingesta y dbt sobre la base descargada.
2. Compruebe si `data/f1_market.duckdb` cambió.
3. Si cambió, haga commit y push del archivo actualizado.

El workflow necesita permiso de escritura sobre el contenido del repositorio para hacer ese push. Consulta la [documentación de GitHub sobre `GITHUB_TOKEN`](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).

Streamlit Community Cloud puede detectar el cambio en el repositorio y actualizar la app. Consulta [cómo Streamlit actualiza las apps conectadas a GitHub](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app).

## 4. Elegir cuándo corre

La ingesta descarga precios alrededor de cada carrera, y el modelo necesita un cierre bursátil posterior a la fecha de carrera. Un horario de lunes de madrugada puede ejecutarse antes de que algunos mercados hayan cerrado. Primero puedes probar el workflow manualmente desde la pestaña **Actions**; luego programa una ejecución semanal que dé tiempo a que esos precios estén disponibles.

El archivo del workflow debe estar en `.github/workflows/` y en la rama predeterminada. Los horarios se interpretan en UTC por defecto y pueden retrasarse durante periodos de mucha carga. Consulta la [documentación de eventos programados de GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events).

## Lista de verificación

- [ ] Corregir la inserción de `df_tickers` para usar `raw_ticker_data`.
- [ ] Darle al runner una configuración de dbt que apunte a la base DuckDB correcta.
- [ ] Ejecutar el pipeline y dbt en Actions.
- [ ] Guardar el DuckDB actualizado en el repositorio con los permisos necesarios.
- [ ] Probar una ejecución manual y confirmar que Streamlit muestra los datos actualizados.
- [ ] Configurar el horario semanal después de validar el proceso.
