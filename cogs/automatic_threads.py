import discord
from discord.ext import commands
from core.config import ART_CHANNEL_ID, PROJECTS_CHANNEL_ID, DESKTOPS_CHANNEL_ID
from utils.message import has_attachments, has_threadable_link, has_threadable_embed

class AutomaticThreads(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.art_channel_id = int(ART_CHANNEL_ID)
        self.projects_channel_id = int(PROJECTS_CHANNEL_ID)
        self.desktops_channel_id = int(DESKTOPS_CHANNEL_ID)

        # Sacar o añadir IDs de canales aca para deshabilitar/habilitar la creación automatica
        self.channels = [self.art_channel_id, self.projects_channel_id, self.desktops_channel_id]

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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (not isinstance(message.channel, discord.TextChannel)):
            return
        
        # Reviso si el ID del canal NO coincide con algún ID de los canales donde se deben crear los hilos
        if not message.channel.id in self.channels:
            return

        if message.author.bot:
            return
        
        if not self.is_art_message(message):
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
