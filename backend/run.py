#!/usr/bin/env python3
"""
TaskPulse - AI Assistant - Application Runner
Simple script to run the FastAPI application
"""

import uvicorn
from app.config import settings


def main():
    """Run the FastAPI application."""
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ████████╗ █████╗ ███████╗██╗  ██╗██████╗ ██╗   ██╗██╗     ███████╗███████╗   ║
║   ╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║   ██║██║     ██╔════╝██╔════╝   ║
║      ██║   ███████║███████╗█████╔╝ ██████╔╝██║   ██║██║     ███████╗█████╗     ║
║      ██║   ██╔══██║╚════██║██╔═██╗ ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝     ║
║      ██║   ██║  ██║███████║██║  ██╗██║     ╚██████╔╝███████╗███████║███████╗   ║
║      ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝   ║
║                              █████╗ ██╗                       ║
║                             ██╔══██╗██║                       ║
║                             ███████║██║                       ║
║                             ██╔══██║██║                       ║
║                             ██║  ██║██║                       ║
║                             ╚═╝  ╚═╝╚═╝                       ║
║                                                                  ║
║         The Intelligent Task Completion Engine                   ║
║         "Don't Just Track Work. Finish It."                      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

    Starting {settings.APP_NAME} v{settings.APP_VERSION}
    Environment: {settings.ENVIRONMENT}
    Debug: {settings.DEBUG}
    AI Provider: {settings.AI_PROVIDER}

    Server running at: http://{settings.HOST}:{settings.PORT}
    API Documentation: http://{settings.HOST}:{settings.PORT}/docs
    """)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()
