import discord
from typing import List, Callable

class Paginator(discord.ui.View):
    def __init__(
        self,
        items: List,
        embed_fn: Callable[[List, int], discord.Embed],
        page: int = 1,
        per_page: int = 25,
        **kwargs
    ):
        super().__init__(timeout=None)
        self.items = items
        self.embed_fn = embed_fn
        self.per_page = per_page
        self.page = page
        
        self.max_page = max(1, -(-len(self.items) // self.per_page))  # ceil div

    @discord.ui.button(label='Prev', style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
        title = interaction.message.embeds[0].title
        await interaction.response.edit_message(
            embed=self.embed_fn(self.items, self.page, title),
            view=Paginator(self.items, self.embed_fn, self.page, self.per_page)
        )

    @discord.ui.button(label='Next', style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.max_page:
            self.page += 1
        title = interaction.message.embeds[0].title
        await interaction.response.edit_message(
            embed=self.embed_fn(self.items, self.page, title),
            view=Paginator(self.items, self.embed_fn, self.page, self.per_page)
        )
