import logging
import asyncpg
from typing import Optional
from src.core.models import AtoOficial

logger = logging.getLogger(__name__)

class PostgresRepository:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.dsn)
            logger.info("Conectado ao PostgreSQL.")

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Conexão com PostgreSQL fechada.")

    async def setup_schema(self):
        """Criação básica da tabela para armazenar os atos processados e a extensão vector."""
        queries = [
            "CREATE EXTENSION IF NOT EXISTS vector;",
            """
            CREATE TABLE IF NOT EXISTS atos_oficiais (
                id SERIAL PRIMARY KEY,
                identificador VARCHAR(255) UNIQUE NOT NULL,
                hash_conteudo VARCHAR(64),
                secretaria TEXT,
                orgao TEXT,
                titulo TEXT,
                texto_limpo TEXT,
                pagina INT,
                motor_extracao VARCHAR(50),
                data_publicacao DATE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS atos_chunks (
                id SERIAL PRIMARY KEY,
                ato_id INT REFERENCES atos_oficiais(id) ON DELETE CASCADE,
                texto_chunk TEXT NOT NULL,
                embedding vector(768),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                id SERIAL PRIMARY KEY,
                polling_interval_minutes INT DEFAULT 60,
                monitoramento_ativo BOOLEAN DEFAULT TRUE,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        if self.pool:
            async with self.pool.acquire() as conn:
                for query in queries:
                    await conn.execute(query)
                
                # Inicializa configurações padrão se a tabela estiver vazia
                count = await conn.fetchval("SELECT COUNT(*) FROM system_settings")
                if count == 0:
                    await conn.execute(
                        "INSERT INTO system_settings (polling_interval_minutes, monitoramento_ativo) VALUES (60, TRUE)"
                    )
                
                logger.info("Schema do banco de dados e pgvector verificados/criados.")
                
                # Migração: Alterar tipos de coluna se já existirem
                await conn.execute("ALTER TABLE atos_oficiais ALTER COLUMN secretaria TYPE TEXT;")
                await conn.execute("ALTER TABLE atos_oficiais ALTER COLUMN orgao TYPE TEXT;")


    async def insert_ato_if_not_exists(self, ato: AtoOficial) -> bool:
        """
        Insere o ato apenas se identificador não existir.
        Retorna True se inseriu, False se foi deduplicado.
        """
        if not self.pool:
            logger.error("Tentativa de insert sem pool conectado.")
            return False

        query = """
            INSERT INTO atos_oficiais (
                identificador, hash_conteudo, secretaria, orgao, 
                titulo, texto_limpo, pagina, motor_extracao, data_publicacao
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9
            )
            ON CONFLICT (identificador) DO NOTHING
            RETURNING id;
        """
        
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchval(
                    query,
                    ato.identificador,
                    ato.hash_conteudo,
                    ato.secretaria,
                    ato.orgao,
                    ato.titulo,
                    ato.texto_limpo,
                    ato.pagina,
                    ato.motor_extracao,
                    ato.metadados.data_publicacao
                )
                
                if result:
                    logger.info(f"Ato {ato.identificador} inserido com ID {result}.")
                    return True
                else:
                    logger.debug(f"Ato {ato.identificador} ignorado (Deduplicação).")
                    return False
                    
            except Exception as e:
                logger.error(f"Erro ao inserir ato no banco: {e}")
                return False

    async def get_ato_id_by_identificador(self, identificador: str) -> Optional[int]:
        """Recupera o ID do ato a partir do identificador."""
        if not self.pool:
            return None
        query = "SELECT id FROM atos_oficiais WHERE identificador = $1;"
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, identificador)

    async def insert_chunk(self, ato_id: int, texto_chunk: str) -> bool:
        """Insere um chunk de texto na base, sem embedding inicialmente."""
        if not self.pool:
            return False
        query = """
            INSERT INTO atos_chunks (ato_id, texto_chunk)
            VALUES ($1, $2) RETURNING id;
        """
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(query, ato_id, texto_chunk)
                return True
            except Exception as e:
                logger.error(f"Erro ao inserir chunk para o ato {ato_id}: {e}")
                return False

    async def get_chunks_without_vectors(self, limit: int = 100) -> list:
        """Busca chunks que ainda não possuem vetor associado."""
        if not self.pool:
            return []
        query = """
            SELECT id, texto_chunk FROM atos_chunks 
            WHERE embedding IS NULL
            ORDER BY criado_em ASC
            LIMIT $1;
        """
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, limit)
            return [{"id": r["id"], "texto_chunk": r["texto_chunk"]} for r in records]

    async def save_chunk_vector(self, chunk_id: int, embedding: list[float]) -> bool:
        """Salva o embedding para um chunk específico."""
        if not self.pool:
            return False
        # Para pgvector, podemos inserir o array diretamente que o asyncpg converte
        query = """
            UPDATE atos_chunks 
            SET embedding = $1::vector 
            WHERE id = $2;
        """
        async with self.pool.acquire() as conn:
            try:
                # O driver do asyncpg pode precisar receber string formata como '[0.1, ...]' ou lista.
                # Se houver problema de tipo, podemos formatar em string: str(embedding)
                embedding_str = str(embedding)
                await conn.execute(query, embedding_str, chunk_id)
                return True
            except Exception as e:
                logger.error(f"Erro ao salvar vetor para o chunk {chunk_id}: {e}")
                return False

    async def search_similar_chunks(self, query_vector: list[float], limit: int = 5) -> list:
        """
        Busca semântica usando Similaridade de Cosseno (<=>).
        Retorna os chunks mais parecidos e os dados dos atos.
        """
        if not self.pool:
            return []
            
        query = """
            SELECT c.id, c.texto_chunk, 1 - (c.embedding <=> $1::vector) AS similarity,
                   a.identificador, a.titulo, a.secretaria, a.orgao, a.data_publicacao
            FROM atos_chunks c
            JOIN atos_oficiais a ON c.ato_id = a.id
            ORDER BY c.embedding <=> $1::vector
            LIMIT $2;
        """
        async with self.pool.acquire() as conn:
            try:
                embedding_str = str(query_vector)
                records = await conn.fetch(query, embedding_str, limit)
                results = []
                for r in records:
                    results.append({
                        "chunk_id": r["id"],
                        "texto_chunk": r["texto_chunk"],
                        "similaridade": r["similarity"],
                        "ato_identificador": r["identificador"],
                        "ato_titulo": r["titulo"],
                        "ato_secretaria": r["secretaria"],
                        "ato_orgao": r["orgao"],
                        "data_publicacao": str(r["data_publicacao"])
                    })
                return results
            except Exception as e:
                logger.error(f"Erro na busca semântica: {e}")
                return []

    async def get_settings(self) -> dict:
        """Recupera as configurações atuais do sistema."""
        if not self.pool:
            return {"polling_interval_minutes": 60, "monitoramento_ativo": True}
        query = "SELECT polling_interval_minutes, monitoramento_ativo FROM system_settings LIMIT 1;"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query)
            if row:
                return dict(row)
            return {"polling_interval_minutes": 60, "monitoramento_ativo": True}

    async def update_settings(self, polling: int, ativo: bool) -> bool:
        """Atualiza as configurações do sistema."""
        if not self.pool:
            return False
        query = """
            UPDATE system_settings 
            SET polling_interval_minutes = $1, monitoramento_ativo = $2, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = (SELECT id FROM system_settings LIMIT 1);
        """
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(query, polling, ativo)
                return True
            except Exception as e:
                logger.error(f"Erro ao atualizar configurações: {e}")
                return False

    async def get_inventory_stats(self) -> list:
        """Retorna estatísticas de ingestão agregadas por data de publicação."""
        if not self.pool:
            return []
        query = """
            SELECT 
                data_publicacao,
                COUNT(id) as total_atos,
                SUM((SELECT COUNT(*) FROM atos_chunks WHERE ato_id = atos_oficiais.id)) as total_chunks,
                MAX(criado_em) as ultima_ingestao
            FROM atos_oficiais
            GROUP BY data_publicacao
            ORDER BY data_publicacao DESC;
        """
        async with self.pool.acquire() as conn:
            try:
                records = await conn.fetch(query)
                return [dict(r) for r in records]
            except Exception as e:
                logger.error(f"Erro ao buscar inventário: {e}")
                return []
