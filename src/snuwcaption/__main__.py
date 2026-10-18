import logging
import os
import uvicorn
from .service import Settings, create_app


def main():
    from .logging_setup import configure
    configure()
    try:
        app = create_app(Settings.from_env())
        host = os.getenv('CAPTION_HOST', '127.0.0.1')
        port = int(os.getenv('CAPTION_PORT', '8010'))
        if not 1 <= port <= 65535:
            raise ValueError('Invalid CAPTION_PORT')
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    logging.info('SNUWCANVAS CAPTION API | %s:%s', host, port)
    uvicorn.run(app, host=host, port=port, workers=1, access_log=False, log_level='warning',
                proxy_headers=False, server_header=False, timeout_keep_alive=5,
                limit_concurrency=16, h11_max_incomplete_event_size=16384)


if __name__ == '__main__':
    main()
