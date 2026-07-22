from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List, Dict, Any
import json
import logging
from app.services.ai_service import ExerciseTracker

router = APIRouter(prefix="/websocket", tags=["websocket"])

logger = logging.getLogger(__name__)

@router.websocket("/ws/{exercise_name}")
async def websocket_endpoint(
    websocket: WebSocket,
    exercise_name: str,
    variation: str = "Standard"
):
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for exercise: {exercise_name}, variation: {variation}")
    
    # Initialize our AI Exercise Tracker
    tracker = ExerciseTracker(exercise_name=exercise_name, target_variation=variation)
    
    try:
        while True:
            # Receive coordinate payload from client
            data_str = await websocket.receive_text()
            payload = json.loads(data_str)
            
            # Expecting payload: { "landmarks": [ { "x": ..., "y": ..., "z": ... }, ... ] }
            landmarks = payload.get("landmarks", [])
            
            if not landmarks:
                await websocket.send_json({"error": "Missing landmarks array"})
                continue
                
            # Process coordinates in AI engine
            analysis_result = tracker.process_landmarks(landmarks)
            
            # Send real-time feedback back to client
            await websocket.send_json(analysis_result)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for exercise: {exercise_name}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close()
        except Exception:
            pass
