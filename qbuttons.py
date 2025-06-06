import discord
import embeds as qb


class Qbuttons(discord.ui.View):
    def __init__(self, queue, page=1):
        super().__init__(timeout=None)
        self.page = page
        self.queue = queue

    @discord.ui.button(label='Prev', style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            page = self.page - 1
        else:
            page = self.page

        await interaction.response.edit_message(
            embed=qb.queue_list(self.queue, page),
            view=Qbuttons(self.queue, page)
        )

    @discord.ui.button(label='Next', style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        max_page = -(-len(self.queue) // 25)
        if self.page < max_page:
            page = self.page + 1
        else:
            page = self.page

        await interaction.response.edit_message(
            embed=qb.queue_list(self.queue, page),
            view=Qbuttons(self.queue, page)
        )
