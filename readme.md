# Wiimu

## Formato .env
```ENV
BOT_TOKEN=
APPLICATION_ID=
GUILD_ID=
DATABASE_PATH=core\Wiimu_Production_Database.sqlite3
```

> [!NOTE]
> Ninguna variable de entorno es opcional. Están las justas y necesarias para no necesitar tener nada en memoria y tampoco tener la necesidad de persistir cosas en una base de datos.

## Manual

### Agregar modulos
<p>Para agregar o quitar modulos, hay que ir al archivo <a href=".\core\config.py">config.py</a> <i>(core/config.py)</i>, y en la variable <b>BOT_FEATURES</b> agregar o quitar el string que corresponda al modulo ubicado en la carpeta <i>cogs</i>. Para habilitar o deshabilitar modulos durante la ejecución actual de Wiimu, hay comandos que empiezan con el prefijo <b>/dev</b> ej: <code>/dev_enable_cog</code></p>

### Modificar colores de los embeds
<p>Para cambiar los colores de los embeds que manda el bot, tenes que ir al archivo <a href=".\utils\colors.py">colors.py</a> <i>(utils/colors.py)</i>, es bastante intuitivo asi que no creo que requiera mas explicación.</p>

### Crear nuevos modulos (cogs)
<p>Para poder crear nuevos modulos que no sean utilidades, si no mas bien features del bot, recomiendo tomar de ejemplo <a href=".\cogs\automatic_threads.py">automatic_threads.py</a> <i>(cogs/art_threads.py)</i> ya que es el modulo mas corto.<p>

> [!NOTE]
> Es necesario tener el metodo setup al final del codigo para que discord pueda detectar el <b>cog</b> y cargarlo.
> Una vez que lo programes no olvidarse de habilitarlo. (<a href="#agregar-modulos">Agregar/quitar modulos</a>)
