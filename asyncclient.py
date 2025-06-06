import asyncssh
import aiomysql
import socket


class AsyncClient:
    def __init__(self, ssh_host, ssh_username, ssh_password,
                 remote_bind_address, db_user, db_pass, db_name,
                 local_port=3307, keepalive_interval=None):
        
        self.ssh_host = ssh_host
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.remote_bind_address = remote_bind_address
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.local_port = local_port
        self.keepalive_interval = keepalive_interval

        self.tunnel = None
        self.pool = None

    async def connect_ssh_tunnel(self):
        """Establish a new SSH tunnel."""
        try:
            self.tunnel = await asyncssh.connect(
                self.ssh_host,
                username=self.ssh_username,
                password=self.ssh_password,
                known_hosts=None,
                keepalive_interval=self.keepalive_interval
            )

            await self.tunnel.forward_local_port(
                '127.0.0.1', self.local_port,
                self.remote_bind_address, 3306
            )

        except Exception as e:
            print(f"[SSH ERROR] Failed to establish SSH tunnel: {e}")
            raise

    async def ensure_ssh_tunnel(self):
        """Ensure SSH tunnel is active and reconnect if needed."""
        if self.tunnel is None or self.tunnel._conn is None or self.tunnel._conn.is_closing():
            await self.close_ssh_tunnel()
            await self.connect_ssh_tunnel()

    async def connect_db_pool(self):
        """Create a new database connection pool."""
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
            print(f"[DB ERROR] Failed to create DB pool: {e}")
            raise

    async def ensure_db_pool(self):
        """Ensure the DB pool is active and reconnect if needed."""
        if self.pool is None or self.pool._closed:
            await self.close_db_pool()
            await self.connect_db_pool()

    async def get_cursor(self):
        """Get a MySQL cursor, reconnecting if needed."""
        try:
            await self.ensure_db_pool()
            conn = await self.pool.acquire()
            cursor = await conn.cursor()
            return cursor, conn

        except (asyncssh.DisconnectError,
                ConnectionResetError,
                OSError,
                aiomysql.OperationalError,
                socket.error) as e:

            print(f"[RECOVERY] Connection dropped or reset: {e}. Reconnecting...")
            await self.close()
            return await self.get_cursor()

    async def close_db_pool(self):
        """Close the DB pool safely."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    async def close_ssh_tunnel(self):
        """Close the SSH tunnel safely."""
        if self.tunnel:
            self.tunnel.close()
            await self.tunnel.wait_closed()
            self.tunnel = None

    async def close(self):
        """Close both SSH tunnel and DB pool."""
        await self.close_db_pool()
        await self.close_ssh_tunnel()
