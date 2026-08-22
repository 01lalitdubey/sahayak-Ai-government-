import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.translation.executor import TranslationExecutor
from app.services.translation.queue_manager import queue_manager, QueueState
from app.models.enums import TranslationJobStatusEnum

@pytest.fixture
def mock_provider():
    provider = AsyncMock()
    provider.translate_json.return_value = {"name": "Test translated"}
    provider.provider_name = "mock_provider"
    return provider

@pytest.fixture
def reset_queue():
    queue_manager.reset()
    yield
    queue_manager.reset()

@pytest.mark.asyncio
async def test_queue_pause_resume(reset_queue):
    queue_manager.state.status = TranslationJobStatusEnum.RUNNING
    
    queue_manager.pause()
    assert queue_manager.state.status == TranslationJobStatusEnum.PAUSED
    assert queue_manager.state._last_pause_stamp is not None
    
    # simulate some time paused
    await asyncio.sleep(0.1)
    
    queue_manager.resume()
    assert queue_manager.state.status == TranslationJobStatusEnum.RUNNING
    assert queue_manager.state.paused_time > 0
    assert queue_manager.state._last_pause_stamp is None

@pytest.mark.asyncio
async def test_queue_cancel(reset_queue):
    queue_manager.state.status = TranslationJobStatusEnum.RUNNING
    await queue_manager.state.queue.put(("scheme_1", "hi"))
    await queue_manager.state.queue.put(("scheme_2", "hi"))
    
    queue_manager.cancel()
    assert queue_manager.state.status == TranslationJobStatusEnum.CANCELLED
    assert queue_manager.state.queue.empty()

@pytest.mark.asyncio
async def test_process_empty_translation_validation(mock_provider, reset_queue):
    # Setup mock to return empty
    mock_provider.translate_json.return_value = {}
    
    executor = TranslationExecutor(provider=mock_provider)
    
    with patch("app.services.translation.executor.AsyncSessionLocal") as mock_session_maker:
        session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = session
        
        # Mock scheme
        mock_scheme = MagicMock()
        session.get.return_value = mock_scheme
        
        # Mock DB result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result
        
        with patch("app.services.translation.executor._extract_translation_fields", return_value={"name": "test"}):
            with patch("app.services.translation.executor._calculate_checksum", return_value="checksum"):
                # Should raise ValueError on empty translation
                with pytest.raises(ValueError, match="Empty translation output"):
                    await executor._process_single_translation("some-uuid", "hi")
