import logging

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

from config import _settings
from api_server.whatsapp import send_whatsapp_message
from api_server.database import get_users_tasks_by_date
from api_server.tasky_ai import generate_daily_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/daily-summary")
async def send_daily_summary(req: Request):
    try:
        body = await req.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    date = body.get("date")
    if not date:
        raise HTTPException(status_code=400, detail="Missing 'date' in request body")
    
    try:
        users_tasks = get_users_tasks_by_date(date)
        
        import asyncio

        daily_summaries = []
        send_tasks = []

        for user in users_tasks:
            phone_number = user["phone_number"]
            contact_name = user["contact_name"]
            tasks = user["tasks"]

            if not tasks:
                message = f"Hello {contact_name}, You got no tasks today. ENJOY!!!"
            else:
                task_list = "\n".join([f"- {task['title']} (Due: {task['due_dt']})" for task in tasks])
                message = generate_daily_summary(
                    date=date,
                    user_name=contact_name,
                    tasks=task_list
                )

            daily_summaries.append({
                "phone_number": phone_number,
                "message": message
            })

            send_tasks.append(
                send_whatsapp_message(
                    phone_number=phone_number,
                    message=message,
                    settings=_settings
                )
            )

        await asyncio.gather(*send_tasks)

        return JSONResponse(status_code=HTTP_200_OK,
                            content={"status": "success", "details" : "Daily summaries sent"}
        )
    
    except Exception as e:
        logger.error(f"Error sending daily summaries: {e}", exc_info=True)
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                            content={"status": "error", "details": "Failed to send daily summaries"})

if __name__ == "__main__":
    port = _settings.PORT or 8080
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)