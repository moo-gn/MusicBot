import discord
import embeds as qb
    

    
# view which initialize component part of the list function
class Qbuttons(discord.ui.View):
    def __init__(self, queue,page = 1):
        super().__init__(timeout=None)
        self.page = page
        self.queue = queue

    @discord.ui.button(label='prev', style=discord.ButtonStyle.grey)
    async def prev(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page > 1:
            page = (self.page - 1)
        else:
            page = self.page
        await interaction.response.edit_message(embed = qb.queue_list(self.queue, page), view = Qbuttons(self.queue, page))

        
        
    @discord.ui.button(label='next', style=discord.ButtonStyle.grey)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page < -(-len(self.queue)//25):
            page = (self.page + 1) 
        else:
            page = self.page
        await interaction.response.edit_message(embed = qb.queue_list(self.queue, page), view = Qbuttons(self.queue, page))

