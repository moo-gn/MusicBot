import asyncio
import asyncssh
import aiomysql


class AsyncClient:
    def __init__(self, ssh_host, ssh_username, ssh_password,
                 remote_bind_address, db_user, db_pass, db_name,
                 local_port=3307, set_keepalive=None):
        
        self.ssh_host = ssh_host
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.remote_bind_address = remote_bind_address
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.local_port = local_port
        self.set_keepalive = set_keepalive

        self.tunnel = None
        self.pool = None

    async def ensure_ssh_tunnel(self):
        if not self.tunnel or self.tunnel._conn._transport._protocol._closing:
            try:
                self.tunnel = await asyncssh.connect(
                    self.ssh_host,
                    username=self.ssh_username,
                    password=self.ssh_password,
                    known_hosts=None,
                    keepalive_interval=self.set_keepalive if self.set_keepalive else None
                )

                await self.tunnel.forward_local_port(
                    '127.0.0.1',        # listen_host (local)
                    self.local_port,     # listen_port (local port)
                    self.remote_bind_address,  # dest_host (remote host)
                    3306                 # dest_port (remote MySQL port)
                )

            except Exception as e:
                print(f"Failed to establish SSH tunnel: {e}")
                raise

    async def ensure_db_pool(self):
        if not self.pool or self.pool._closed:
            try:
                await self.ensure_ssh_tunnel()

                self.pool = await aiomysql.create_pool(
                    host='127.0.0.1',
                    port=self.local_port,
                    user=self.db_user,
                    password=self.db_pass,
                    db=self.db_name,
                    autocommit=True,
                    charset='utf8mb4'
                )
            except Exception as e:
                print(f"Failed to create DB pool: {e}")
                raise

    async def get_cursor(self):
        await self.ensure_db_pool()
        conn = await self.pool.acquire()
        cursor = await conn.cursor()
        return cursor, conn 

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

        if self.tunnel:
            self.tunnel.close()
            await self.tunnel.wait_closed()