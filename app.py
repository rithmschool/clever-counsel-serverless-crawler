from chalice import Chalice, IAMAuthorizer
from chalicelib.web_capture import capture_sos, capture_locality

app = Chalice(app_name="clever-counsel-lambda")
authorizer = IAMAuthorizer()


@app.route("/sos", methods=["POST"], authorizer=authorizer)
def add_sos_screenshot():
    """ Runs sos webcapture fxns with Selenium/Chromedriver 
        current_request: {
            entity_number, # CA SOS entity number
            s3_directory 
        }
    """
    data = app.current_request.json_body
    resp = capture_sos(**data)

    if resp.get("success"):
        # let the main API know that you"ve completed the task
        return {"data": resp, "status": 200}

    # else, you failed somehow
    return {"status": 400}


@app.route("/locality", methods=["POST"], authorizer=authorizer)
def add_locality():
    """ Runs locality webcapture fxn  with Selenium/Chromedriver """

    data = app.current_request.json_body
    resp = capture_locality(**data)
    if not resp:
        return {"error": "locality of business not found", "status": 404}

    return {"data": resp["data"], "status": 200}


@app.route("/test")
def test():
    return "hello"
