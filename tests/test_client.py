import pytest
from unittest.mock import patch, AsyncMock

from src.core.client import DOEBahiaClient

@pytest.mark.asyncio
async def test_fetch_content_success():
    """Testa se o client baixa conteúdo corretamente lidando com rate limit e httpx"""
    client = DOEBahiaClient()
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"PDF_BYTES"
        mock_get.return_value.headers = {"Content-Type": "application/pdf"}
        
        # Mudar a política do Jitter para não travar os testes unitários
        with patch("src.core.client.apply_jitter", new_callable=AsyncMock):
            content, ctype = await client.fetch_content("mock_123")
        
        assert content == b"PDF_BYTES"
        assert ctype == "application/pdf"
        
    await client.close()

@pytest.mark.asyncio
async def test_fetch_content_retry_on_500():
    """Testa se o Exponential Backoff funciona para erros 500 do servidor"""
    client = DOEBahiaClient()
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Retorna 500 na primeira vez, e 200 na segunda
        mock_response_500 = AsyncMock()
        mock_response_500.status_code = 500
        
        mock_response_200 = AsyncMock()
        mock_response_200.status_code = 200
        mock_response_200.content = b"HTML_BYTES"
        mock_response_200.headers = {"Content-Type": "text/html"}
        
        mock_get.side_effect = [mock_response_500, mock_response_200]
        
        with patch("src.core.client.apply_jitter", new_callable=AsyncMock), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            content, ctype = await client.fetch_content("mock_456")
            
        assert content == b"HTML_BYTES"
        assert ctype == "text/html"
        assert mock_get.call_count == 2
        
    await client.close()
