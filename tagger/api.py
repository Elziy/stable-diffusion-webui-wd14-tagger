from typing import Callable
from threading import Lock
from secrets import compare_digest

from modules import shared
from modules.api.api import decode_base64_to_image
from modules.call_queue import queue_lock
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from tagger import utils
from tagger import api_models as models


class Api:
    def __init__(self, app: FastAPI, queue_lock: Lock, prefix: str = None) -> None:
        if shared.cmd_opts.api_auth:
            self.credentials = dict()
            for auth in shared.cmd_opts.api_auth.split(","):
                user, password = auth.split(":")
                self.credentials[user] = password

        self.app = app
        self.queue_lock = queue_lock
        self.prefix = prefix

        self.add_api_route(
            'interrogate',
            self.endpoint_interrogate,
            methods=['POST'],
            response_model=models.TaggerInterrogateResponse
        )

        self.add_api_route(
            'interrogators',
            self.endpoint_interrogators,
            methods=['GET'],
            response_model=models.InterrogatorsResponse
        )

    def auth(self, creds: HTTPBasicCredentials = Depends(HTTPBasic())):
        if creds.username in self.credentials:
            if compare_digest(creds.password, self.credentials[creds.username]):
                return True

        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={
                "WWW-Authenticate": "Basic"
            })

    def add_api_route(self, path: str, endpoint: Callable, **kwargs):
        if self.prefix:
            path = f'{self.prefix}/{path}'

        if shared.cmd_opts.api_auth:
            return self.app.add_api_route(path, endpoint, dependencies=[Depends(self.auth)], **kwargs)
        return self.app.add_api_route(path, endpoint, **kwargs)

    def endpoint_interrogate(self, req: models.TaggerInterrogateRequest):
        if req.image is None:
            raise HTTPException(404, 'Image not found')

        if req.model not in utils.interrogators.keys():
            raise HTTPException(404, 'Model not found')

        if req.unload_model_after_running is None:
            req.unload_model_after_running = False

        image = decode_base64_to_image(req.image)
        interrogator = utils.interrogators[req.model]
        unload_model_after_running = req.unload_model_after_running

        with self.queue_lock:
            ratings, general_tag, character_tag = interrogator.interrogate(image)
            if unload_model_after_running:
                interrogator.unload()

        processed_general_tags = interrogator.postprocess_tags(
            tags=general_tag,
            threshold=req.threshold,
            replace_underscore=req.replace_underscore,
            replace_underscore_excludes=req.replace_underscore_excludes
        )

        processed_character_tags = interrogator.postprocess_tags(
            tags=character_tag,
            threshold=req.threshold,
            replace_underscore=req.replace_underscore,
            replace_underscore_excludes=req.replace_underscore_excludes
        )

        processed_tags = processed_general_tags.copy()
        processed_tags.update(processed_character_tags)

        return models.TaggerInterrogateResponse(
            ratings=ratings,
            tags=processed_tags,
            general_tags=processed_general_tags,
            character_tags=processed_character_tags
        )

    def endpoint_interrogators(self):
        return models.InterrogatorsResponse(
            models=list(utils.interrogators.keys())
        )


def on_app_started(_, app: FastAPI):
    Api(app, queue_lock, '/tagger/v1')
