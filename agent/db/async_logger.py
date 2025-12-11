
import asyncio
import logging
from typing import Any, Optional
from .engine import get_session
from .repository import AgentLogRepository

class AsyncLogManager:
    """
    Manages asynchronous logging to the database to prevent blocking the main event loop.
    Uses an asyncio Queue to buffer logs and a background worker to flush them.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncLogManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.queue = asyncio.Queue()
        self.worker_task = None
        self.running = False
        self._initialized = True
        
    async def start(self):
        """Start the background flusher task."""
        if self.running:
            return
            
        self.running = True
        self.worker_task = asyncio.create_task(self._flush_worker())
        print("[AsyncLogger] Background worker started.")
        
    async def stop(self):
        """Stop the worker and flush remaining logs."""
        self.running = False
        if self.worker_task:
            await self.queue.join() # Wait for queue to empty
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            print("[AsyncLogger] Background worker stopped.")
            
    def log(self, action_type: str, output: str, node_name: str = "system", 
            tool_name: Optional[str] = None, reasoning: Optional[str] = None, 
            error: Optional[str] = None, cycle_id: Optional[str] = None):
        """
        Queue a log entry for background writing. Non-blocking.
        """
        entry = {
            "action_type": action_type,
            "output": output,
            "node_name": node_name,
            "tool_name": tool_name,
            "reasoning": reasoning,
            "error": error,
            "cycle_id": cycle_id
        }
        
        try:
            self.queue.put_nowait(entry)
        except Exception as e:
            print(f"[AsyncLogger] Failed to queue log: {e}")

    async def _flush_worker(self):
        """Background loop to process queue items."""
        while self.running:
            try:
                # Get item (wait up to 1s)
                entry = await self.queue.get()
                
                # Process strictly
                await self._write_to_db(entry)
                
                # Mark done
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[AsyncLogger] Worker error: {e}")
                
    async def _write_to_db(self, entry: dict):
        """Write a single entry to DB (SYNC wrapper inside threadpool could be better, but simple calls are fast enough if batched.. actually let's just do sync call here as it's in a separate task but still blocks loop if main thread. Optimally run in executor)"""
        
        # To truly not block the loop, we should run the blocking DB IO in a thread
        try:
            await asyncio.to_thread(self._sync_save, entry)
        except Exception as e:
             print(f"[AsyncLogger] DB Write Failed: {e}")

    def _sync_save(self, entry: dict):
        """Synchronous DB save."""
        with get_session() as session:
            try:
                AgentLogRepository.log(
                    session,
                    action_type=entry["action_type"],
                    output=entry["output"],
                    node_name=entry["node_name"],
                    tool_name=entry["tool_name"],
                    reasoning=entry["reasoning"],
                    error=entry["error"]
                )
            except Exception as e:
                print(f"[AsyncLogger] Repository Error: {e}")

# Global Accessor
async_logger = AsyncLogManager()
