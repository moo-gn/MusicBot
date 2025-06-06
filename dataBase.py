from asyncclient import AsyncClient 
import embeds as  qb
import sys
sys.path.append("..")
import credentials

# start the connection to pythonanywhere
client = AsyncClient(	
							ssh_host=(credentials.ssh_website),
							ssh_username=credentials.ssh_username, 
							ssh_password=credentials.ssh_password,
							remote_bind_address=credentials.remote_bind_address,
							local_port= 3306,
							db_user=credentials.db_user,
							db_pass=credentials.db_passwd,
							db_name=credentials.db,
							set_keepalive=30,
						)



async def db_add_song(song: str, link: str,):
	"""
	Adds a song to the database. If the song exists it increments its uses by 1 
	"""
	# Init the cursor and database
	cursor, con = await client.get_cursor()

	try:
		await cursor.execute("SELECT song FROM music WHERE song=%s;", (song,))
		exists = await cursor.fetchall()
		if exists:
			await cursor.execute("UPDATE music SET uses=uses+1 WHERE song=%s;", (song,))
		else:
			await cursor.execute("INSERT INTO music(song, uses, link) values (%s, %s, %s);", (song, 1, link))
	except Exception as e:
		print(e)
	finally:
		# Close the database
		await cursor.close()
		client.pool.release(con)

# Intilizie cursor and db
async def random_songs(ctx, amount = 5):
	cursor, con = await client.get_cursor()
	try:
		await cursor.execute("SELECT song,link FROM music WHERE uses > 5 AND blacklisted=0 ORDER BY rand() LIMIT %s;", (amount,))
	except:
		await ctx.send(embed=qb.send_msg('**[ERROR 404]** Invalid number'))
	finally:
		# Close the database
		data = await cursor.fetchall()  
		await cursor.close()
		client.pool.release(con)
		return list(data)
	
async def artist_songs(ctx, msg, amount = 10):
	cursor, con = await client.get_cursor()
	try:         
		# #Select all the current data in the database and display it         
		await cursor.execute("SELECT song,link FROM music WHERE song LIKE %s ORDER BY rand() LIMIT %s;", (f"%{msg}%", amount))         
	except Exception as e:
		print(e)
		await ctx.send(embed=qb.send_msg('**[ERROR 404]** Invalid name'))      
	finally:
		data = await cursor.fetchall()
		await cursor.close()
		client.pool.release(con)
		if not data:
			await ctx.send(embed=qb.send_msg('**[ERROR 404]** artist not found'))
		else:
			return list(data)
		
async def blacklist(ctx, msg):
	cursor, con = await client.get_cursor()

	try:
		await cursor.execute("SELECT blacklisted FROM music WHERE song=%s;", (msg,))
		result = await cursor.fetchone()
		if not result:
			await ctx.send(embed=qb.send_msg(f"{msg} doesn't exist in The Database"))
			return
		
		blacklisted = result[0] ^ 1
		await cursor.execute("UPDATE music SET blacklisted=%s WHERE song=%s;", (blacklisted, {msg}))
		if blacklisted:
			await ctx.send(embed=qb.send_msg(f"Blacklisted {msg}!"))
		else:
			await ctx.send(embed=qb.send_msg(f"removed {msg} from Blacklist!"))		
	except Exception as e:
		await ctx.send(embed=qb.send_msg(f'**[Unkown ERROR]** {e}'))     
	finally:
		await cursor.close()
		client.pool.release(con)

async def get_blacklist(ctx):
	cursor, con = await client.get_cursor()
	try:
		await cursor.execute(f"select song FROM music WHERE blacklisted=1 ORDER BY song;")
	except Exception as e:
		await ctx.send(embed=qb.send_msg(f'**[Unkown ERROR]** {e}'))      
	finally:
		# Close the database
		data = await cursor.fetchall()  
		await cursor.close()
		client.pool.release(con)
		return list(data)
