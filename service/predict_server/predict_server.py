from fastapi import FastAPI, Request
# from prometheus_fastapi_instrumentator import Instrumentator
import logging

import inference

# logging settings
py_logger = logging.getLogger(__name__)
py_logger.setLevel(logging.INFO)
py_handler = logging.FileHandler(f"./log/{__name__}.log", mode='a')
py_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
py_handler.setFormatter(py_formatter)
py_logger.addHandler(py_handler)
py_logger.info(" ")
py_logger.info("##############################################################")
py_logger.info(f"Start logging for module {__name__}...")

app = FastAPI()
# Instrumentator().instrument(app).expose(app)


@app.post("/predict")
async def get_X(request: Request):
    data = await request.json()
    X = data['X']
    y = data['y']
    print(X, y)
    prediction = inference.predict(X, y)
    py_logger.info(f"True values: {y}")
    py_logger.info(f"Predicted values: {prediction}")
    py_logger.info("------------------------------------------------")

    return prediction
