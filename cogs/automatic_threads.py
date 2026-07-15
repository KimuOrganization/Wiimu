import discord
from discord.ext import commands
from core.config import ART_CHANNEL_ID, PROJECTS_CHANNEL_ID, DESKTOPS_CHANNEL_ID, COMMAND_CHANNEL_ID
from utils.message import has_attachments, has_threadable_link, has_threadable_embed
import time
from datetime import timedelta, datetime, timezone
from collections import deque
from utils.colors import ModerationColors


class AutomaticThreads(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.art_channel_id = int(ART_CHANNEL_ID)
        self.projects_channel_id = int(PROJECTS_CHANNEL_ID)
        self.desktops_channel_id = int(DESKTOPS_CHANNEL_ID)

        # Sacar o añadir IDs de canales aca para deshabilitar/habilitar la creación automatica
        self.channels = [self.art_channel_id, self.projects_channel_id, self.desktops_channel_id]

        # Va a contener info de los usuarios que utilicen el canal de forma indebida
        self.infractions = {}

        # Ventana de tiempo para acumular infracciones
        self.infraction_window = timedelta(minutes=30)

        # Duración de la sanción por el uso inapropiado reiterado del canal
        self.timeout_duration : int = 60 # minutos

        # Razón del timeout
        self.timeout_reason : str = "Se enviaron demasiados mensajes inválidos en el canal {}."

    """ 
    En el caso de que se agreguen mas canales en los que se deban generar hilos automaticamente
    hay que agregar un case, que corresponda al id del canal, y cuyo valor devuelto sea el prefijo
    que queres que tenga el hilo en el titulo.
    Ejemplos: 'Arte' de {nombre} | 'Proyecto' de {nombre} | 'Desktop' de {nombre}
    """
    def get_thread_prefix(self, id:int):
        if (id == self.art_channel_id):
            return "Arte"
        elif(id == self.projects_channel_id):
            return "Proyecto"
        elif(id == self.desktops_channel_id):
            return "Desktop"
        else:
            raise RuntimeError("[ERROR(cogs/automatic_threads.py - thread_channel)] Ha ocurrido un error al intentar detectar el prefijo para el hilo. (Revisar casos del condicional)")
                
    def is_art_message(self, message: discord.Message) -> bool:
        if has_attachments(message):
            return True
        if has_threadable_link(message.content):
            return True
        if has_threadable_embed(message):
            return True
        return False

    async def notify_infraction(self, message: discord.Message):
        channel = message.channel
        member = message.author
        guild = message.guild

        # Evitar warnings de pylance
        if not isinstance(channel, discord.TextChannel) or not isinstance(member, discord.Member) or guild is None:
            return 

        dm_embed = discord.Embed(
            title="Tu mensaje fue eliminado",
            description=(
                f"Se elimino tu mensaje en {channel.mention}.\n\n"
                "**Para publicar:**\n"
                "• Envía una imagen, video, archivo o cualquier otro adjunto.\n"
                "• También puedes enviar un enlace (URL).\n\n"
                "**Si deseas responder a una publicación:**\n"
                "Hazlo dentro del hilo correspondiente, no directamente en el canal.\n\n"
                "Si continúas enviando mensajes invalidos repetidamente, "
                "podrías recibir un timeout automático."
            ),
            color=ModerationColors.PRIVATE_MESSAGE,
            timestamp=datetime.now()
        )
        dm_embed.set_author(name=guild.name,icon_url=guild.icon.url if guild.icon else None)
        dm_embed.set_footer(text="Este mensaje es automático")
        
        try:
            await member.send(embed=dm_embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    async def log_timeout(self, message: discord.Message):
        channel = message.channel
        member = message.author
        guild = message.guild

        # Calcular la hora de finalización del timeout
        until = datetime.now(timezone.utc) + timedelta(minutes=self.timeout_duration)

        # Evitar warnings de pylance
        if not isinstance(channel, discord.TextChannel) or not isinstance(member, discord.Member) or not isinstance(guild, discord.Guild):
            return 

        log_channel = guild.get_channel(int(COMMAND_CHANNEL_ID))

        # Evitar warnings de pylance
        if not isinstance(log_channel, discord.TextChannel):
            print("NOT A LOG TEXT CHANNEL")
            return

        log_embed = discord.Embed(
            title="Usuario aislado",
            description=(
                f"**Razón:** {self.timeout_reason.format(channel.mention) or 'No especificada'}\n"
                f"**Moderador/a:** {self.bot.user.mention}\n"
                f"**Hasta:** <t:{int(until.timestamp())}:f>"),
            timestamp=datetime.now(),
            color=ModerationColors.MUTE,
        )
        log_embed.add_field(name="Aislado", value=f"\u2800\u2800`{member.name} [{member.id}]`", inline=False)
        log_embed.set_author(name=f"{guild.name}", icon_url=guild.icon.url if guild.icon else None)
        log_embed.set_footer(text="ID: "+str(self.bot.user.id))

        try:
            # Enviar Log
            await log_channel.send(embed=log_embed)
        except (discord.Forbidden, discord.HTTPException):
            pass


    async def handle_art_violation(self, message: discord.Message):
        channel = message.channel
        member = message.author
        
        # Evitar warnings de pylance
        if not isinstance(channel, discord.TextChannel) or not isinstance(member, discord.Member):
            return 

        user_id : int = member.id
        now : float = time.monotonic()

        warnings : deque[float] = self.infractions.setdefault(user_id, deque(maxlen=3))

        # Eliminar infracciones con mas de 5 minutos
        # (se ejecuta como mucho 3 veces, no es un loop constante)
        while warnings and now - warnings[0] > self.infraction_window.total_seconds():
            warnings.popleft()

        warnings.append(now)

        if len(warnings) == 1:
            # Notificar al usuario del uso apropiado del canal y posible sanción
            await self.notify_infraction(message)

        # 3 infracciones en el lapso de 5 minutos
        if len(warnings) >= 3:
            try:
                # Enviar log del timeout
                await self.log_timeout(message)

                # Realizar timeout
                await member.timeout(
                    timedelta(minutes=self.timeout_duration),
                    reason=self.timeout_reason.format(channel.mention)
                )
            except (discord.Forbidden, discord.HTTPException):
                pass

            # Limpiar historial
            del self.infractions[user_id]

    @commands.Cog.listener("on_message")
    async def on_automatic_threads_message(self, message: discord.Message):
        if (not isinstance(message.channel, discord.TextChannel)):
            return
        
        # Reviso si el ID del canal NO coincide con algún ID de los canales donde se deben crear los hilos
        if not message.channel.id in self.channels:
            return

        if message.author.bot:
            return
        
        if not self.is_art_message(message):
            await self.handle_art_violation(message)
            await message.delete()
            return
        
        if (message.author.display_name != message.author.name):
            name = f"{message.author.display_name} ({message.author.name})"
        else:
            name = f"{message.author.display_name}"

        thread_name = f"{self.get_thread_prefix(message.channel.id)} de {name}"
        # Para evitar errores, revisar que el nombre no supere el tamaño maximo
        if (len(thread_name) > 100):
            thread_name = thread_name[:100]

        await message.create_thread(
            name=thread_name,
            reason=f"Creación automatica de Hilo en canal de {message.channel.name}" 
        )

async def setup(bot):
    await bot.add_cog(AutomaticThreads(bot))
